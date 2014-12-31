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

"""Generate HTTP tests from YAML files

Each HTTP request is its own TestCase and can be requested to be run in
isolation from other tests. If it is member of a sequence of requests,
prior requests will be run.

A sequence is represented by an ordered list in a single YAML file.

Each sequence becomes a TestSuite.

An entire directory of YAML files is a TestSuite of TestSuites.
"""

import glob
import inspect
import os
from unittest import suite
import uuid

import httplib2
import wsgi_intercept
from wsgi_intercept import httplib2_intercept
import yaml

from .suite import GabbiSuite
from .case import HTTPTestCase


# Empty test from which all others inherit
BASE_TEST = {
    'name': '',
    'desc': '',
    'ssl': False,
    'redirects': False,
    'method': 'GET',
    'url': '',
    'status': '200',
    'request_headers': {},
    'response_headers': {},
    'response_strings': None,
    'response_json_paths': None,
    'data': '',
}


class TestBuilder(type):
    """Metaclass to munge a dynamically created test.
    """

    required_attributes = {'has_run': False}

    def __new__(mcs, name, bases, attributes):
        attributes.update(mcs.required_attributes)
        return type.__new__(mcs, name, bases, attributes)


def build_tests(path, loader, host=None, port=8001, intercept=None,
                test_file_name=None, fixture_module=None):
    """Read YAML files from a directory to create tests.

    Each YAML file represents an ordered sequence of HTTP requests.
    """
    top_suite = suite.TestSuite()
    http = httplib2.Http()

    if test_file_name is None:
        test_file_name = inspect.stack()[1]
        test_file_name = os.path.splitext(os.path.basename(
            test_file_name[1]))[0]

    # Return an empty suite if we have no host to access, either via
    # a real host or an intercept
    if not host and not intercept:
        return top_suite

    if intercept:
        host = install_intercept(intercept, port)

    test_directory = path
    path = '%s/*.yaml' % path

    key_test = set(BASE_TEST.keys())

    for test_file in glob.iglob(path):
        file_suite = GabbiSuite()
        test_yaml = load_yaml(test_file)
        test_data = test_yaml['tests']
        fixtures = test_yaml.get('fixtures', None)
        test_base_name = os.path.splitext(os.path.basename(test_file))[0]

        # Set defaults from BASE_TESTS the update those defaults
        # which any defaults set in the YAML file.
        base_test_data = dict(BASE_TEST)
        base_test_data.update(test_yaml.get('defaults', {}))

        fixture_classes = []
        if fixtures and fixture_module:
            for fixture_class in fixtures:
                fixture_classes.append(getattr(fixture_module, fixture_class))

        prior_test = None
        for test_datum in test_data:
            test = dict(base_test_data)
            test.update(test_datum)
            test_name = '%s_%s_%s' % (test_file_name,
                                      test_base_name,
                                      test['name'].lower().replace(' ', '_'))
            if set(test.keys()) != key_test:
                raise ValueError('Invalid Keys in test %s' % test_name)

            # Use metaclasses to build a class of the necessary type
            # with relevant arguments.
            klass = TestBuilder(test_name, (HTTPTestCase,),
                                {'test_data': test,
                                 'test_directory': test_directory,
                                 'fixtures': fixture_classes,
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
