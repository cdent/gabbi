# Copyright 2014, 2015 Red Hat
#
# Authors: Chris Dent <chdent@redhat.com>
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
made using httplib2. Assertions are made against the reponse.
"""

from __future__ import print_function

import copy
import functools
import json
import os
import re
import sys

import wsgi_intercept
import jsonpath_rw
import six
from six.moves.urllib import parse as urlparse
from testtools import testcase

from gabbi import utils

REPLACERS = [
    'SCHEME',
    'NETLOC',
    'ENVIRON',
    'LOCATION',
    'HEADERS',
    'RESPONSE',
]


# Empty test from which all others inherit
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
    'data': '',
    'xfail': False,
    'skip': '',
}


def potentialFailure(func):
    """Decorate a test method that is expected to fail if 'xfail' is true."""
    @functools.wraps(func)
    def wrapper(self):
        if self.test_data['xfail']:
            try:
                func(self)
            except Exception:
                raise testcase._ExpectedFailure(sys.exc_info())
            raise testcase._UnexpectedSuccess
        else:
            func(self)
    return wrapper


class HTTPTestCase(testcase.TestCase):
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
                    message = getattr(self, method)(message)
            except TypeError:
                # Message is not a string
                pass

        return message

    def _assert_response(self):
        """Compare the response with expected data."""

        test = self.test_data
        response = self.response

        # Never accept a 500
        if response['status'] == '500':
            raise ServerError(self.output)

        self._test_status(test['status'], response['status'])

        for handler in self.response_handlers:
            handler(self)

    def _environ_replace(self, message):
        """Replace an indicator in a message with the environment value."""
        return re.sub(r"\$ENVIRON\['([^']+)'\]",
                      self._environ_replacer, message)

    @staticmethod
    def _environ_replacer(match):
        """Replace a regex match with an environment value.

        Let KeyError raise if variable not present.
        """
        environ_name = match.group(1)
        return os.environ[environ_name]

    @staticmethod
    def extract_json_path_value(data, path):
        """Extract the value at JSON Path path from the data.

        The input data is a Python datastructre, not a JSON string.
        """
        path_expr = jsonpath_rw.parse(path)
        matches = [match.value for match in path_expr.find(data)]
        try:
            return matches[0]
        except IndexError:
            raise ValueError(
                "JSONPath '%s' failed to match on data: '%s'" % (path, data))

    def _headers_replace(self, message):
        """Replace a header indicator in a message with that headers value from
        the prior request.
        """
        return re.sub(r"\$HEADERS\['([^']+)'\]",
                      self._header_replacer, message)

    def _header_replacer(self, match):
        """Replace a regex match with the value of a prior header."""
        header_key = match.group(1)
        return self.prior.response[header_key.lower()]

    def _json_replacer(self, match):
        """Replace a regex match with the value of a JSON Path."""
        path = match.group(1)
        return str(self.extract_json_path_value(self.prior.json_data, path))

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
        return message.replace('$NETLOC', self.netloc)

    def _parse_url(self, url, ssl=False):
        """Create a url from test data.

        If provided with a full URL, just return that. If SSL is requested
        set the scheme appropriately.

        Scheme and netloc are saved for later use in comparisons.
        """
        parsed_url = urlparse.urlsplit(url)
        url_scheme = parsed_url[0]
        scheme = 'http'
        netloc = self.host

        if not url_scheme:
            if self.port:
                netloc = '%s:%s' % (self.host, self.port)
            if ssl:
                scheme = 'https'
            full_url = urlparse.urlunsplit((scheme, netloc, parsed_url[2],
                                            parsed_url[3], ''))
            self.scheme = scheme
            self.netloc = netloc
        else:
            full_url = url
            self.scheme = url_scheme
            self.netloc = parsed_url[1]

        return full_url

    def _response_replace(self, message):
        """Replace a JSON Path from the prior request with a value."""
        return re.sub(r"\$RESPONSE\['([^']+)'\]",
                      self._json_replacer, message)

    def _run_request(self, url, method, headers, body):
        """Run the http request and decode output.

        The call to make the request will catch a WSGIAppError from
        wsgi_intercept so that the real traceback from a catastrophic
        error in the intercepted app can be examined.
        """

        try:
            response, content = self.http.request(
                url,
                method=method,
                headers=headers,
                body=body
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
        decoded_output = utils.decode_content(response, content)
        if (decoded_output and
                'application/json' in response.get('content-type', '')):
            self.json_data = json.loads(decoded_output)
        self.output = decoded_output

    def _run_test(self):
        """Make an HTTP request and compare the response with expectations."""
        test = self.test_data

        base_url = self.replace_template(test['url'])
        full_url = self._parse_url(base_url, test['ssl'])

        method = test['method'].upper()
        headers = test['request_headers']
        for name in headers:
            headers[name] = self.replace_template(headers[name])

        if test['data']:
            body = self._test_data_to_string(
                test['data'], headers.get('content-type', ''))
        else:
            body = ''

        # Reset follow_redirects with every go.
        self.http.follow_redirects = False
        if test['redirects']:
            self.http.follow_redirects = True

        # Print some information about this request is asked.
        if test['verbose']:
            print('\n###########################')
            print('%s %s' % (method, full_url))
            for key in headers:
                print('%s: %s' % (key, headers[key]))

        self._run_request(full_url, method, headers, body)
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
        self.assertIn(observed_status, statii)


class ServerError(Exception):
    """A catchall ServerError."""
    pass
