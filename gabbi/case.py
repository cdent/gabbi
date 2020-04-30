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
made using urllib3. Assertions are made against the response.
"""

from collections import OrderedDict
import copy
import functools
import os
import re
import sys
import time
import unittest
from unittest import result as unitresult

import six
from six.moves import http_cookies
from six.moves.urllib import parse as urlparse
import wsgi_intercept

from gabbi import __version__
from gabbi import exception
from gabbi.handlers import base
from gabbi import utils


MAX_CHARS_OUTPUT = 2000

REPLACERS = [
    'SCHEME',
    'NETLOC',
    'ENVIRON',
    'LOCATION',
    'COOKIE',
    'LAST_URL',
    'URL',
    'HEADERS',
    'RESPONSE',
]

# Basic test template determining both valid keys and default values
BASE_TEST = {
    'name': '',
    'desc': '',
    'verbose': False,
    'cert_validate': True,
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
    'use_prior_test': True,
}


def potentialFailure(func):
    """Decorate a test method that is expected to fail if 'xfail' is true."""
    @functools.wraps(func)
    def wrapper(self):
        if self.test_data['xfail']:
            try:
                func(self)
            except Exception:
                self._addExpectedFailure(self.result, sys.exc_info())
            else:
                self._addUnexpectedSuccess(self.result)
        else:
            func(self)
    return wrapper


def _is_complex_type(data):
    """If data is a list or dict return True."""
    return isinstance(data, list) or isinstance(data, dict)


class HTTPTestCase(unittest.TestCase):
    """Encapsulate a single HTTP request as a TestCase.

    If the test is a member of a sequence of requests, ensure that prior
    tests are run.

    To keep the test harness happy we need to make sure the setUp and
    tearDown are only run once.
    """

    base_test = copy.copy(BASE_TEST)

    def setUp(self):
        self._fixture_cleanups = []
        if not self.has_run:
            super(HTTPTestCase, self).setUp()
            for fixture in self.inner_fixtures:
                f = fixture()
                f.setUp()
                # add fixture to front of list so we unwind them FILO in
                # tearDown
                self._fixture_cleanups.insert(0, f)

    def tearDown(self):
        if not self.has_run:
            super(HTTPTestCase, self).tearDown()
        self.has_run = True
        # Clean up an inner fixtures.
        for fixture in self._fixture_cleanups:
            fixture.cleanUp()

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

        if (self.prior and not self.prior.has_run and
                self.test_data['use_prior_test']):
            # Use a different result so we don't count this test
            # in the results.
            self.prior.run(unitresult.TestResult())
        self._run_test()

    def get_content_handler(self, content_type):
        """Determine the content handler for this media type."""
        for handler in self.content_handlers:
            if handler.accepts(content_type):
                return handler
        return None

    def replace_template(self, message, escape_regex=False):
        """Replace magic strings in message."""
        if isinstance(message, dict):
            for k in message:
                message[k] = self.replace_template(message[k],
                                                   escape_regex=escape_regex)
            return message

        if isinstance(message, list):
            return [self.replace_template(line, escape_regex=escape_regex)
                    for line in message]

        for replacer in REPLACERS:
            template = '$%s' % replacer
            method = '_%s_replace' % replacer.lower()
            try:
                if template in message:
                    try:
                        replace = getattr(self, method)
                        message = replace(message, escape_regex=escape_regex)
                    except (KeyError, AttributeError, ValueError) as exc:
                        raise AssertionError(
                            'unable to replace %s in %s, data unavailable: %s'
                            % (template, message, exc))
            except TypeError:
                # Message is not a string
                pass

        return message

    def load_data_file(self, filename):
        """Read a file from the current test directory."""
        return self._load_data_file(filename)

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

    @staticmethod
    def _regex_replacer(replacer, escape_regex):
        """Wrap a replacer function to escape return values in a regex."""
        if escape_regex:
            @functools.wraps(replacer)
            def replace(match):
                return re.escape(replacer(match))

            return replace
        else:
            return replacer

    def _environ_replace(self, message, escape_regex=False):
        """Replace an indicator in a message with the environment value.

        If value can be a number, cast it as such. If value is a form of
        "null", "true", or "false" cast it to None, True, False.
        """
        value = re.sub(self._replacer_regex('ENVIRON'),
                       self._regex_replacer(self._environ_replacer,
                                            escape_regex),
                       message)
        try:
            if '.' in value:
                value = float(value)
            else:
                value = int(value)
            return value
        except ValueError:
            pass
        if value.lower() == "false":
            return False
        if value.lower() == "true":
            return True
        if value.lower() == "null":
            return None
        return value

    @staticmethod
    def _environ_replacer(match):
        """Replace a regex match with an environment value.

        Let KeyError raise if variable not present.
        """
        environ_name = match.group('arg')
        return os.environ[environ_name]

    def _cookie_replace(self, message, escape_regex=False):
        """Replace $COOKIE in a message.

        With cookie data from set-cookie in the prior request.
        """
        return re.sub(self._simple_replacer_regex('COOKIE'),
                      self._regex_replacer(self._cookie_replacer,
                                           escape_regex),
                      message)

    def _cookie_replacer(self, match):
        """Replace a regex match with the cookie of a previous response."""
        case = match.group('case')
        if case:
            referred_case = self.history[case]
        else:
            referred_case = self.prior
        response_cookies = referred_case.response['set-cookie']
        cookies = http_cookies.SimpleCookie()
        cookies.load(response_cookies)
        cookie_string = cookies.output(attrs=[], header='', sep=',').strip()
        return cookie_string

    def _headers_replace(self, message, escape_regex=False):
        """Replace a header indicator in a message.

        Replace it with the header's value from the prior request.
        """
        return re.sub(self._replacer_regex('HEADERS'),
                      self._regex_replacer(self._header_replacer,
                                           escape_regex),
                      message)

    def _header_replacer(self, match):
        """Replace a regex match with the value of a prior header."""
        header_key = match.group('arg')
        case = match.group('case')
        if case:
            referred_case = self.history[case]
        else:
            referred_case = self.prior
        return referred_case.response[header_key.lower()]

    def _last_url_replace(self, message, escape_regex=False):
        """Replace $LAST_URL in a message.

        With the URL used in the prior request.
        """
        last_url = self.prior.url
        if escape_regex:
            last_url = re.escape(last_url)
        return message.replace('$LAST_URL', last_url)

    def _url_replace(self, message, escape_regex=False):
        """Replace $URL in a message.

        With the URL used in a previous request.
        """
        return re.sub(self._simple_replacer_regex('URL'),
                      self._regex_replacer(self._url_replacer,
                                           escape_regex),
                      message)

    def _url_replacer(self, match):
        """Replace a regex match with the value of a previous url."""
        case = match.group('case')
        if case:
            referred_case = self.history[case]
        else:
            referred_case = self.prior
        return referred_case.url

    def _location_replace(self, message, escape_regex=False):
        """Replace $LOCATION in a message.

        With the location header from a previous request.
        """
        return re.sub(self._simple_replacer_regex('LOCATION'),
                      self._regex_replacer(self._location_replacer,
                                           escape_regex),
                      message)

    def _location_replacer(self, match):
        """Replace a regex match with the value of a previous location."""
        case = match.group('case')
        if case:
            referred_case = self.history[case]
        else:
            referred_case = self.prior
        return referred_case.location

    def _load_data_file(self, filename):
        """Read a file from the current test directory."""
        path = os.path.join(self.test_directory, filename)
        has_dir_traversal = os.path.relpath(
            path, start=self.test_directory).startswith(os.pardir)
        if has_dir_traversal:
            raise ValueError(
                'Attempted loading of data file outside test directory: %s'
                % filename)
        with open(path, mode='rb') as data_file:
            return data_file.read()

    def _netloc_replace(self, message, escape_regex=False):
        """Replace $NETLOC with the current host and port."""
        netloc = self.netloc
        if self.prefix:
            netloc = '%s%s' % (netloc, self.prefix)
        if escape_regex:
            netloc = re.escape(netloc)
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

    _history_regex = (
        r"(?:\$HISTORY\[(?P<quote1>['\"])(?P<case>.+?)(?P=quote1)\]\.)??"
    )

    @staticmethod
    def _replacer_regex(key):
        """Compose a regular expression for test template variables."""
        case = HTTPTestCase._history_regex
        return r"%s\$%s\[(?P<quote>['\"])(?P<arg>.+?)(?P=quote)\]" % (
            case, key)

    @staticmethod
    def _simple_replacer_regex(key):
        """Compose a regular expression for simple variable replacement."""
        case = HTTPTestCase._history_regex
        return r"%s\$%s" % (case, key)

    def _response_replace(self, message, escape_regex=False):
        """Replace a content path with the value from a previous response.

        If the match would replace the entire message, then don't cast it
        to a string.
        """
        regex = self._replacer_regex('RESPONSE')
        match = re.match('^%s$' % regex, message)
        if match:
            return self._response_replacer(match, preserve=True)
        return re.sub(regex,
                      self._regex_replacer(self._response_replacer,
                                           escape_regex),
                      message)

    def _response_replacer(self, match, preserve=False):
        """Replace a regex match with the value from a previous response."""
        response_path = match.group('arg')
        case = match.group('case')
        if case:
            referred_case = self.history[case]
        else:
            referred_case = self.prior
        replacer_class = self.get_content_handler(
            referred_case.response.get('content-type'))
        # If no handler can be found use the null replacer,
        # which returns "foo" when "$RESPONSE['foo']".
        replacer_class = replacer_class or base.ContentHandler
        result = replacer_class.replacer(
            referred_case.response_data, response_path)
        if preserve:
            return result
        else:
            return six.text_type(result)

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
        loader_class = self.get_content_handler(self.content_type)
        if decoded_output and loader_class:
            # save structured response data
            self.response_data = loader_class.loads(decoded_output)
        else:
            self.response_data = None
        self.output = decoded_output

    def _replace_headers_template(self, test_name, headers):
        replaced_headers = {}

        try:
            for name in headers:
                replaced_name = self.replace_template(name)
                replaced_headers[replaced_name] = self.replace_template(
                    headers[name]
                )
        except TypeError as exc:
            raise exception.GabbiFormatError(
                'malformed headers in test %s: %s' % (test_name, exc))

        return replaced_headers

    def _run_test(self):
        """Make an HTTP request and compare the response with expectations."""
        test = self.test_data

        base_url = self.replace_template(test['url'])
        # Save the URL after replacers but before query_parameters
        self.url = base_url
        full_url = self._parse_url(base_url)

        # Replace variables in headers with variable values. This includes both
        # in the header key and the header value.
        test['request_headers'] = self._replace_headers_template(
            test['name'], test['request_headers'])
        test['response_headers'] = self._replace_headers_template(
            test['name'], test['response_headers'])

        method = test['method'].upper()
        headers = test['request_headers']

        if test['data'] != '':
            body = self._test_data_to_string(
                test['data'],
                utils.extract_content_type(headers, default='')[0])
        else:
            body = ''

        # ensure body is bytes, encoding as UTF-8 because that's
        # what we do here
        if isinstance(body, six.text_type):
            body = body.encode('UTF-8')

        if test['poll']:
            count = int(float(self.replace_template(
                test['poll'].get('count', 1))))
            delay = float(self.replace_template(test['poll'].get('delay', 1)))
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

    def _scheme_replace(self, message, escape_regex=False):
        """Replace $SCHEME with the current protocol."""
        scheme = re.escape(self.scheme) if escape_regex else self.scheme
        return message.replace('$SCHEME', scheme)

    def _test_data_to_string(self, data, content_type):
        """Turn the request data into a string.

        If the data is not binary, replace template strings.

        If the result of the template handling is not a string,
        run the result through the dumper.
        """
        dumper_class = self.get_content_handler(content_type)
        if not _is_complex_type(data):
            if isinstance(data, six.string_types) and data.startswith('<@'):
                info = self.load_data_file(data.replace('<@', '', 1))
                if utils.not_binary(content_type):
                    data = six.text_type(info, 'UTF-8')
                else:
                    # Return early we are binary content
                    return info
        else:
            # We have a complex data structure, try to dump it.
            if dumper_class:
                data = self.replace_template(data)
                data = dumper_class.dumps(data, test=self)
            else:
                raise ValueError(
                    'unable to process data to %s' % content_type)

        data = self.replace_template(data)

        # If the result after template handling is not a string, dump
        # it if there is a suitable dumper.
        if dumper_class and not isinstance(data, six.string_types):
            # If there are errors dumping we want them to raise to the
            # test harness.
            data = dumper_class.dumps(data, test=self)
        return data

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
        if utils.not_binary(utils.parse_content_type(self.content_type)[0]):
            if expected in iterable:
                return

            if self.response_data:
                dumper_class = self.get_content_handler(self.content_type)
                if dumper_class:
                    full_response = dumper_class.dumps(self.response_data,
                                                       pretty=True, test=self)
                else:
                    full_response = self.output
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
