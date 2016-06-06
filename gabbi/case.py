#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""A single HTTP request represented as a subclass of ``unittest.TestCase``

The test case encapsulates the request headers and body and expected
response headers and body. When the test is run an HTTP request is
made using urllib3. Assertions are made against the reponse.
"""

from collections import OrderedDict
import copy
import functools
import json
import os
import re
import sys
import time
import unittest
from unittest import case

import six
from six.moves import http_cookies
from six.moves.urllib import parse as urlparse
import wsgi_intercept

from gabbi import __version__
from gabbi import json_parser
from gabbi import utils


MAX_CHARS_OUTPUT = 2000

REPLACERS = [
    'SCHEME',
    'NETLOC',
    'ENVIRON',
    'LOCATION',
    'COOKIE',
    'LAST_URL',
    'HEADERS',
    'RESPONSE',
]

# Basic test template determining both valid keys and default values
BASE_TEST = {
    'name': '',
    'desc': '',
    'verbose': False,
    'ssl': False,
    'redirects': False,
    'method': 'GET',
    'url': '',
    'status': '200',
    'request_headers': {},
    'query_parameters': {},
    'data': '',
    'xfail': False,
    'skip': '',
    'poll': {},
}


def potentialFailure(func):
    """Decorate a test method that is expected to fail if 'xfail' is true."""
    @functools.wraps(func)
    def wrapper(self):
        if self.test_data['xfail']:
            try:
                func(self)
            except Exception:
                if hasattr(case, '_ExpectedFailure'):
                    raise case._ExpectedFailure(sys.exc_info())
                else:
                    self._addExpectedFailure(self.result, sys.exc_info())
            else:
                if hasattr(self, '_addUnexpectedSuccess'):
                    self._addUnexpectedSuccess(self.result)
                else:
                    raise case._UnexpectedSuccess
        else:
            func(self)
    return wrapper


class HTTPTestCase(unittest.TestCase):
    """Encapsulate a single HTTP request as a TestCase.

    If the test is a member of a sequence of requests, ensure that prior
    tests are run.

    To keep the test harness happy we need to make sure the setUp and
    tearDown are only run once.
    """

    response_handlers = []
    base_test = copy.copy(BASE_TEST)

    def setUp(self):
        if not self.has_run:
            super(HTTPTestCase, self).setUp()

    def tearDown(self):
        if not self.has_run:
            super(HTTPTestCase, self).tearDown()
        self.has_run = True

    def run(self, result=None):
        """Store the current result handler on this test."""
        self.result = result
        super(HTTPTestCase, self).run(result)

    @potentialFailure
    def test_request(self):
        """Run this request if it has not yet run.

        If there is a prior test in the sequence, run it first.
        """
        if self.has_run:
            return

        if self.test_data['skip']:
            self.skipTest(self.test_data['skip'])

        if self.prior and not self.prior.has_run:
            self.prior.run()
        self._run_test()

    def replace_template(self, message):
        """Replace magic strings in message."""
        if isinstance(message, dict):
            for k in message:
                message[k] = self.replace_template(message[k])
            return message

        for replacer in REPLACERS:
            template = '$%s' % replacer
            method = '_%s_replace' % replacer.lower()
            try:
                if template in message:
                    try:
                        message = getattr(self, method)(message)
                    except (KeyError, AttributeError, ValueError) as exc:
                        raise AssertionError(
                            'unable to replace %s in %s, data unavailable: %s'
                            % (template, message, exc))
            except TypeError:
                # Message is not a string
                pass

        return message

    def _assert_response(self):
        """Compare the response with expected data."""
        self._test_status(self.test_data['status'], self.response['status'])

        for handler in self.response_handlers:
            handler(self)

    def _clean_query_value(self, value):
        """Clean up a single query from query_parameters."""
        value = self.replace_template(value)
        # stringify ints in Python version independent fashion
        value = '%s' % value
        value = value.encode('UTF-8')
        return value

    def _environ_replace(self, message):
        """Replace an indicator in a message with the environment value."""
        value = re.sub(self._replacer_regex('ENVIRON'),
                       self._environ_replacer, message)
        if value == "False":
            return False
        if value == "True":
            return True
        return value

    @staticmethod
    def _environ_replacer(match):
        """Replace a regex match with an environment value.

        Let KeyError raise if variable not present.
        """
        environ_name = match.group('arg')
        return os.environ[environ_name]

    @staticmethod
    def extract_json_path_value(data, path):
        """Extract the value at JSON Path path from the data.

        The input data is a Python datastructure, not a JSON string.
        """
        path_expr = json_parser.parse(path)
        matches = [match.value for match in path_expr.find(data)]
        if matches:
            if len(matches) > 1:
                return matches
            else:
                return matches[0]
        else:
            raise ValueError(
                "JSONPath '%s' failed to match on data: '%s'" % (path, data))

    def _cookie_replace(self, message):
        """Replace $COOKIE in a message.

        With cookie data from set-cookie in the prior request.
        """
        response_cookies = self.prior.response['set-cookie']
        cookies = http_cookies.SimpleCookie()
        cookies.load(response_cookies)
        cookie_string = cookies.output(attrs=[], header='', sep=',').strip()
        return message.replace('$COOKIE', cookie_string)

    def _headers_replace(self, message):
        """Replace a header indicator in a message with that headers value from
        the prior request.
        """
        return re.sub(self._replacer_regex('HEADERS'),
                      self._header_replacer, message)

    def _header_replacer(self, match):
        """Replace a regex match with the value of a prior header."""
        header_key = match.group('arg')
        return self.prior.response[header_key.lower()]

    def _json_replacer(self, match):
        """Replace a regex match with the value of a JSON Path."""
        path = match.group('arg')
        return str(self.extract_json_path_value(self.prior.json_data, path))

    def _last_url_replace(self, message):
        """Replace $LAST_URL in a message.

        With the URL used in the prior request.
        """
        return message.replace('$LAST_URL', self.prior.url)

    def _location_replace(self, message):
        """Replace $LOCATION in a message.

        With the location header from the prior request.
        """
        return message.replace('$LOCATION', self.prior.location)

    def _load_data_file(self, filename):
        """Read a file from the current test directory."""
        path = os.path.join(self.test_directory, os.path.basename(filename))
        with open(path, mode='rb') as data_file:
            return data_file.read()

    def _netloc_replace(self, message):
        """Replace $NETLOC with the current host and port."""
        netloc = self.netloc
        if self.prefix:
            netloc = '%s%s' % (netloc, self.prefix)
        return message.replace('$NETLOC', netloc)

    def _parse_url(self, url):
        """Create a url from test data.

        If provided with a full URL, just return that. If SSL is requested
        set the scheme appropriately.

        Scheme and netloc are saved for later use in comparisons.
        """
        query_params = self.test_data['query_parameters']
        ssl = self.test_data['ssl']

        parsed_url = urlparse.urlsplit(url)
        if not parsed_url.scheme:
            full_url = utils.create_url(url, self.host, port=self.port,
                                        prefix=self.prefix, ssl=ssl)
            # parse again to set updated netloc and scheme
            parsed_url = urlparse.urlsplit(full_url)

        self.scheme = parsed_url.scheme
        self.netloc = parsed_url.netloc

        if query_params:
            query_string = self._update_query_params(parsed_url.query,
                                                     query_params)
        else:
            query_string = parsed_url.query

        return urlparse.urlunsplit((parsed_url.scheme, parsed_url.netloc,
                                    parsed_url.path, query_string, ''))

    @staticmethod
    def _replacer_regex(key):
        """Compose a regular expression for test template variables."""
        return r"\$%s\[(?P<quote>['\"])(?P<arg>.+?)(?P=quote)\]" % key

    def _response_replace(self, message):
        """Replace a JSON Path from the prior request with a value."""
        return re.sub(self._replacer_regex('RESPONSE'),
                      self._json_replacer, message)

    def _run_request(self, url, method, headers, body, redirect=False):
        """Run the http request and decode output.

        The call to make the request will catch a WSGIAppError from
        wsgi_intercept so that the real traceback from a catastrophic
        error in the intercepted app can be examined.
        """

        if 'user-agent' not in (key.lower() for key in headers):
            headers['user-agent'] = "gabbi/%s (Python urllib3)" % __version__

        try:
            response, content = self.http.request(
                url,
                method=method,
                headers=headers,
                body=body,
                redirect=redirect
            )
        except wsgi_intercept.WSGIAppError as exc:
            # Extract and re-raise the wrapped exception.
            six.reraise(exc.exception_type, exc.exception_value,
                        exc.traceback)

        # Set headers and location attributes for follow on requests
        self.response = response
        if 'location' in response:
            self.location = response['location']

        # Decode and store response
        decoded_output = utils.decode_response_content(response, content)
        self.content_type = response.get('content-type', '').lower()
        if (decoded_output and
                ('application/json' in self.content_type or
                 '+json' in self.content_type)):
            self.json_data = json.loads(decoded_output)
        else:
            self.json_data = None
        self.output = decoded_output

    def _run_test(self):
        """Make an HTTP request and compare the response with expectations."""
        test = self.test_data

        base_url = self.replace_template(test['url'])
        # Save the URL after replacers but before query_parameters
        self.url = base_url
        full_url = self._parse_url(base_url)

        method = test['method'].upper()
        headers = test['request_headers']
        for name in headers:
            headers[name] = self.replace_template(headers[name])

        if test['data'] is not '':
            body = self._test_data_to_string(
                test['data'], headers.get('content-type', ''))
        else:
            body = ''

        if test['poll']:
            count = test['poll'].get('count', 1)
            delay = test['poll'].get('delay', 1)
            failure = None
            while count:
                try:
                    self._run_request(full_url, method, headers, body,
                                      redirect=test['redirects'])
                    self._assert_response()
                    failure = None
                    break
                except (AssertionError, utils.ConnectionRefused) as exc:
                    failure = exc

                count -= 1
                time.sleep(delay)

            if failure:
                raise failure
        else:
            self._run_request(full_url, method, headers, body,
                              redirect=test['redirects'])
            self._assert_response()

    def _scheme_replace(self, message):
        """Replace $SCHEME with the current protocol."""
        return message.replace('$SCHEME', self.scheme)

    def _test_data_to_string(self, data, content_type):
        """Turn the request data into a string.

        If the data is not binary, replace template strings.
        """
        if isinstance(data, str):
            if data.startswith('<@'):
                info = self._load_data_file(data.replace('<@', '', 1))
                if utils.not_binary(content_type):
                    try:
                        info = str(info, 'UTF-8')
                    except TypeError:
                        info = info.encode('UTF-8')
                    data = info
                else:
                    return info
        else:
            data = json.dumps(data)
        return self.replace_template(data)

    def _test_status(self, expected_status, observed_status):
        """Confirm we got the expected status.

        If the status contains one or more || then it is treated as a
        list of acceptable statuses.
        """
        expected_status = str(expected_status)
        if '||' in expected_status:
            statii = [stat.strip() for stat in expected_status.split('||')]
        else:
            statii = [expected_status.strip()]

        self.assert_in_or_print_output(observed_status, statii)

    def _update_query_params(self, original_query_string, query_params):
        """Update a query string from query_params dict.

        An OrderedDict is used to allow easier testing and greater
        predictability when doing query updates.
        """
        encoded_query_params = OrderedDict()

        for param, value in query_params.items():
            # isinstance used because we can iter a string
            if isinstance(value, list):
                encoded_query_params[param] = [
                    self._clean_query_value(subvalue)
                    for subvalue in value]
            else:
                encoded_query_params[param] = (
                    self._clean_query_value(value))

        query_string = urlparse.urlencode(
            encoded_query_params, doseq=True)
        if original_query_string:
            query_string = '&'.join([original_query_string, query_string])

        return query_string

    def assert_in_or_print_output(self, expected, iterable):
        """Assert the iterable contains expected or print some output.

        If the output is long, it is limited by either GABBI_MAX_CHARS_OUTPUT
        in the environment or the MAX_CHARS_OUTPUT constant.
        """
        if utils.not_binary(self.content_type):
            if expected in iterable:
                return

            if self.json_data:
                full_response = json.dumps(self.json_data, indent=2,
                                           separators=(',', ': '))
            else:
                full_response = self.output

            max_chars = os.getenv('GABBI_MAX_CHARS_OUTPUT', MAX_CHARS_OUTPUT)
            response = full_response[0:max_chars]
            is_truncated = (len(response) != len(full_response))

            if iterable == self.output:
                msg = "'%s' not found in %s%s" % (
                    expected, response,
                    '\n...truncated...' if is_truncated else ''
                )
            else:
                msg = "'%s' not found in %s, %sresponse:\n%s" % (
                    expected, iterable,
                    'truncated ' if is_truncated else '',
                    response)
            self.fail(msg)
        else:
            self.assertIn(expected, iterable)
