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
import testtools
import wsgi_intercept
from wsgi_intercept import httplib2_intercept
import yaml


# Empty test from which all others inherit
BASE_TEST = {
    'name': '',
    'desc': '',
    'method': 'GET',
    'url': '',
    'status': '200',
    'request_headers': {},
    'response_headers': {},
    'expected': [],
    'expected_json': [],
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

    def _run_test(self):
        """Make an HTTP request."""
        test = self.test_data
        http = self.http

        # TODO(chdent): pass fully qualified straight through
        # TODO(chdent): use urljoin
        full_url = 'http://%s:%s/%s' % (self.host, self.port, test['url'])
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
        self._assert_response(response, content, test['status'],
                              headers=test['response_headers'],
                              expected=test['expected'],
                              expected_json=test['expected_json'])

    def _assert_response(self, response, content, status, headers=None,
                         expected=None, expected_json=None):
        """Compare the results with expected data."""
        if response['status'] == '500':
            raise ServerError(content)

        self.assertEqual(response['status'], str(status))

        if headers:
            for header in headers:
                self.assertEqual(headers[header], response[header])

        output = content.decode('utf-8')
        # Compare strings in response body
        if expected:
            for expect in expected:
                self.assertIn(expect, output)

        # Decode body as JSON and compare.
        # NOTE(chdent): This just here for now to see if it is workable.
        if expected_json:
            response_data = json.loads(output)
            for expect in expected_json:
                self.assertIn(expect, response_data)
                self.assertEqual(expected_json[expect], response_data[expect])


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

    # Return an empty suite if we have no host to access, either via
    # a real host or an intercept
    if not host and not intercept:
        return top_suite

    if intercept:
        host = install_intercept(intercept, port)

    path = '%s/*.yaml' % path

    for test_file in glob.iglob(path):
        file_suite = suite.TestSuite()
        test_data = load_yaml(test_file)
        test_base_name = os.path.splitext(os.path.basename(test_file))[0]

        prior_test = None
        for test_datum in test_data:
            test = dict(BASE_TEST)
            test.update(test_datum)
            test_name = '%s_%s' % (test_base_name,
                                   test['name'].lower().replace(' ', '_'))
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
