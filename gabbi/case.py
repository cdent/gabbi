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

import functools
import json
import os
import re
import sys

import jsonpath_rw
from six.moves.urllib import parse as urlparse
from testtools import testcase


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

    def _assert_response(self, response, content, status, headers=None,
                         expected=None, json_paths=None):
        """Compare the response with expected data."""

        # Decode and store response before anything else
        decoded_output = self._decode_content(response, content)
        if (decoded_output
                and 'application/json' in response.get('content-type', '')):
            self.json_data = json.loads(decoded_output)

        # Never accept a 500
        if response['status'] == '500':
            raise ServerError(content)

        # Always test status
        self._test_status(status, response['status'])

        if headers:
            self._test_headers(headers, response)

        decoded_output = self._decode_content(response, content)

        # Compare strings in response body
        if expected:
            for expect in expected:
                expect = self._replace_response_values(expect)
                self.assertIn(expect, decoded_output)

        # Decode body as JSON and test against json_paths
        if json_paths:
            for path in json_paths:
                match = self._extract_json_path_value(self.json_data, path)
                expected = self._replace_response_values(json_paths[path])
                self.assertEqual(expected, match, 'Unable to match %s as %s'
                                 % (path, expected))

    def _decode_content(self, response, content):
        """Decode content to a proper string."""
        content_type = response.get('content-type',
                                    'application/binary').lower()
        if ';' in content_type:
            content_type, charset = (attr.strip() for attr in
                                     content_type.split(';'))
            charset = charset.split('=')[1].strip()
        else:
            charset = 'utf-8'

        if self._not_binary(content_type):
            return content.decode(charset)
        else:
            return content

    @staticmethod
    def _extract_json_path_value(data, path):
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

    def _load_data_file(self, filename):
        """Read a file from the current test directory."""
        path = os.path.join(self.test_directory, os.path.basename(filename))
        with open(path, mode='rb') as data_file:
            return data_file.read()

    @staticmethod
    def _not_binary(content_type):
        """Decide if something is content we'd like to treat as a string."""
        return (content_type.startswith('text/')
                or content_type.endswith('+xml')
                or content_type.endswith('+json')
                or content_type == 'application/javascript'
                or content_type == 'application/json')

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

    def _replacer(self, match):
        """Replace a regex match with the value of a JSON Path."""
        path = match.group(1)
        return str(self._extract_json_path_value(self.prior.json_data, path))

    def _replace_response_values(self, template):
        """Replace a JSON Path in a template string with its value."""
        try:
            return re.sub(r"\$RESPONSE\['([^']+)'\]", self._replacer, template)
        except TypeError:
            # template is not a string
            return template

    def _run_test(self):
        """Make an HTTP request and compare the response with expectations."""
        test = self.test_data
        http = self.http
        base_url = test['url']

        # Reset follow_redirects with every go.
        http.follow_redirects = False
        if test['redirects']:
            http.follow_redirects = True

        if '$LOCATION' in base_url:
            # Let AttributeError raise
            base_url = base_url.replace('$LOCATION', self.prior.location)

        if '$RESPONSE' in base_url:
            base_url = self._replace_response_values(base_url)

        full_url = self._parse_url(base_url, test['ssl'])
        method = test['method'].upper()
        headers = test['request_headers']

        body = test['data']
        if body:
            body, is_str = self._test_data_to_string(body)
            if self._not_binary(headers['content-type']):
                if is_str:
                    try:
                        body = str(body, 'UTF-8')
                    except TypeError:
                        body = body.encode('UTF-8')
                body = self._replace_response_values(body)

        response, content = http.request(
            full_url,
            method=method,
            headers=headers,
            body=body
        )

        # Set location attribute for follow on requests
        if 'location' in response:
            self.location = response['location']

        self._assert_response(response, content, test['status'],
                              headers=test['response_headers'],
                              expected=test['response_strings'],
                              json_paths=test['response_json_paths'])

    def _test_data_to_string(self, data):
        """Turn the request data into a string."""
        if isinstance(data, str):
            if data.startswith('<@'):
                info = self._load_data_file(data.replace('<@', '', 1))
                return info, True
            else:
                return data, False
        else:
            return json.dumps(data), False

    def _test_headers(self, headers, response):
        """Compare expected headers with actual headers.

        If a header value is wrapped in ``/`` it is treated as a raw
        regular expression.
        """
        for header in headers:
            header_value = headers[header].replace('$SCHEME', self.scheme)
            header_value = header_value.replace('$NETLOC', self.netloc)

            try:
                response_value = response[header]
            except KeyError:
                # Reform KeyError to something more debuggable.
                raise KeyError("'%s' header not available in response keys: %s"
                               % (header, response.keys()))

            if header_value.startswith('/') and header_value.endswith('/'):
                header_value = header_value.strip('/').rstrip('/')
                self.assertRegexpMatches(
                    response_value, header_value,
                    'Expect header %s to match /%s/, got %s' %
                    (header, header_value, response_value))
            else:
                self.assertEqual(header_value, response[header],
                                 'Expect header %s with value %s, got %s' %
                                 (header, header_value, response[header]))

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
