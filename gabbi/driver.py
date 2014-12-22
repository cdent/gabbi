# Copyright 2014 Red Hat
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

"""Generate HTTP tests from YAML files

Each HTTP request is its own TestCase and can be requested to be run in
isolation from other tests. If it is member of a sequence of requests,
prior requests will be run.

A sequence is represented by an ordered list in a single YAML file.

Each sequence becomes a TestSuite.

An entire directory of YAML files is a TestSuite of TestSuites.
"""

import glob
import json
import os
from unittest import suite
import uuid

import httplib2
import jsonpath_rw
from six.moves.urllib import parse as urlparse
import testtools
import wsgi_intercept
from wsgi_intercept import httplib2_intercept
import yaml


# Empty test from which all others inherit
BASE_TEST = {
    'name': '',
    'desc': '',
    'ssl': False,
    'method': 'GET',
    'url': '',
    'status': '200',
    'request_headers': {},
    'response_headers': {},
    'response_strings': None,
    'response_json_paths': None,
    'data': '',
}


class ServerError(Exception):
    """A catchall ServerError."""
    # TODO(chdent): Make a test WSGI app that will cause a 500.
    pass


class HTTPTestCase(testtools.TestCase):
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

    def test_request(self):
        """Run this request if it has not yet run.

        If there is a prior test in the sequence, run it first.
        """
        if self.has_run:
            return
        if self.prior and not self.prior.has_run:
            self.prior.run()
        self._run_test()

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

    def _run_test(self):
        """Make an HTTP request."""
        test = self.test_data
        http = self.http
        base_url = test['url']

        if '$LOCATION' in base_url:
            # Let AttributeError raise
            base_url = base_url.replace('$LOCATION', self.prior.location)

        full_url = self._parse_url(base_url, test['ssl'])
        method = test['method'].upper()
        headers = test['request_headers']
        if method == 'GET' or method == 'DELETE':
            response, content = http.request(
                full_url,
                method=method,
                headers=headers
            )
        else:
            body = test['data'].encode('UTF-8')
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

    def _assert_response(self, response, content, status, headers=None,
                         expected=None, json_paths=None):
        """Compare the results with expected data."""
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
                self.assertIn(expect, decoded_output)

        # Decode body as JSON and compare.
        # NOTE(chdent): This just here for now to see if it is workable.
        if json_paths:
            response_data = json.loads(decoded_output)
            for path in json_paths:
                path_expr = jsonpath_rw.parse(path)
                matches = [match.value for match
                           in path_expr.find(response_data)]
                self.assertEqual(json_paths[path], matches[0])

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

    def _not_binary(self, content_type):
        """Decide if something is content we'd like to treat as a string."""
        return (content_type.startswith('text/')
                or content_type.endswith('+xml')
                or content_type.endswith('+json')
                or content_type == 'application/javascript'
                or content_type == 'application/json')

    def _test_headers(self, headers, response):
        """Compare expected headers with actual headers."""
        for header in headers:
            header_value = headers[header].replace('$SCHEME', self.scheme)
            header_value = header_value.replace('$NETLOC', self.netloc)
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


class TestBuilder(type):
    """Metaclass to munge a dynamically created test.
    """

    required_attributes = {'has_run': False}

    def __new__(mcs, name, bases, attributes):
        attributes.update(mcs.required_attributes)
        return type.__new__(mcs, name, bases, attributes)


def build_tests(path, loader, host=None, port=8001, intercept=None):
    """Read YAML files from a directory to create tests.

    Each YAML file represents an ordered sequence of HTTP requests.
    """
    top_suite = suite.TestSuite()
    http = httplib2.Http()
    http.follow_redirects = False

    # Return an empty suite if we have no host to access, either via
    # a real host or an intercept
    if not host and not intercept:
        return top_suite

    if intercept:
        host = install_intercept(intercept, port)

    path = '%s/*.yaml' % path

    key_test = set(BASE_TEST.keys())

    for test_file in glob.iglob(path):
        file_suite = suite.TestSuite()
        test_yaml = load_yaml(test_file)
        test_data = test_yaml['tests']
        test_base_name = os.path.splitext(os.path.basename(test_file))[0]

        # Set defaults from BASE_TESTS the update those defaults
        # which any defaults set in the YAML file.
        base_test_data = dict(BASE_TEST)
        base_test_data.update(test_yaml.get('defaults', {}))

        prior_test = None
        for test_datum in test_data:
            test = dict(base_test_data)
            test.update(test_datum)
            test_name = '%s_%s' % (test_base_name,
                                   test['name'].lower().replace(' ', '_'))
            if set(test.keys()) != key_test:
                raise ValueError('Invalid Keys in test %s' % test_name)
            # Use metaclasses to build a class of the necessary type
            # with relevant arguments.
            klass = TestBuilder(test_name, (HTTPTestCase,),
                                {'test_data': test,
                                 'http': http,
                                 'host': host,
                                 'port': port,
                                 'prior': prior_test})

            tests = loader.loadTestsFromTestCase(klass)
            this_test = tests._tests[0]
            file_suite.addTest(this_test)
            prior_test = this_test

        top_suite.addTest(file_suite)

    return top_suite


def factory(wsgi_app):
    """Satisfy a bad API."""
    return wsgi_app


def install_intercept(wsgi_callable, port):
    """Install a wsgi-intercept on a random hostname."""
    hostname = str(uuid.uuid4())
    httplib2_intercept.install()
    wsgi_intercept.add_wsgi_intercept(hostname, port, factory(wsgi_callable))
    return hostname


def load_yaml(yaml_file):
    """Read and parse any YAML file. Let exceptions flow where they may."""
    with open(yaml_file) as source:
        return yaml.safe_load(source.read())
