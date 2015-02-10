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
import yaml

from gabbi import case
from gabbi import suite as gabbi_suite


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
    'xfail': False,
    'skip': '',
}


class TestBuilder(type):
    """Metaclass to munge a dynamically created test."""

    required_attributes = {'has_run': False}

    def __new__(mcs, name, bases, attributes):
        attributes.update(mcs.required_attributes)
        return type.__new__(mcs, name, bases, attributes)


def build_tests(path, loader, host=None, port=8001, intercept=None,
                test_loader_name=None, fixture_module=None):
    """Read YAML files from a directory to create tests.

    Each YAML file represents an ordered sequence of HTTP requests.
    """
    top_suite = suite.TestSuite()

    if test_loader_name is None:
        test_loader_name = inspect.stack()[1]
        test_loader_name = os.path.splitext(os.path.basename(
            test_loader_name[1]))[0]

    yaml_file_glob = '%s/*.yaml' % path

    # Return an empty suite if we have no host to access, either via
    # a real host or an intercept
    if host or intercept:
        for test_file in glob.iglob(yaml_file_glob):
            if intercept:
                host = str(uuid.uuid4())
            test_yaml = load_yaml(test_file)
            test_name = '%s_%s' % (test_loader_name,
                                   os.path.splitext(
                                       os.path.basename(test_file))[0])
            file_suite = test_suite_from_yaml(loader, test_name, test_yaml,
                                              path, host, port, fixture_module,
                                              intercept)
            top_suite.addTest(file_suite)
    return top_suite


def load_yaml(yaml_file):
    """Read and parse any YAML file. Let exceptions flow where they may."""
    with open(yaml_file) as source:
        return yaml.safe_load(source.read())


def test_suite_from_yaml(loader, test_base_name, test_yaml, test_directory,
                         host, port, fixture_module, intercept):
    """Generate a TestSuite from YAML data."""

    file_suite = gabbi_suite.GabbiSuite()
    test_data = test_yaml['tests']
    fixtures = test_yaml.get('fixtures', None)

    # Set defaults from BASE_TESTS then update those defaults
    # with any defaults set in the YAML file.
    base_test_data = dict(BASE_TEST)
    base_test_data.update(test_yaml.get('defaults', {}))

    # Establish any fixture classes.
    fixture_classes = []
    if fixtures and fixture_module:
        for fixture_class in fixtures:
            fixture_classes.append(getattr(fixture_module, fixture_class))

    prior_test = None
    for test_datum in test_data:
        test = dict(base_test_data)
        test.update(test_datum)

        if not test['name']:
            raise AssertionError('Test name missing in a test in %s.'
                                 % test_base_name)
        test_name = '%s_%s' % (test_base_name,
                               test['name'].lower().replace(' ', '_'))

        if set(test.keys()) != set(BASE_TEST.keys()):
            raise AssertionError('Invalid test keys used in test: %s'
                                 % test_name)

        # Use metaclasses to build a class of the necessary type
        # and name with relevant arguments.
        klass = TestBuilder(test_name, (case.HTTPTestCase,),
                            {'test_data': test,
                             'test_directory': test_directory,
                             'fixtures': fixture_classes,
                             'http': httplib2.Http(),
                             'host': host,
                             'intercept': intercept,
                             'port': port,
                             'prior': prior_test})

        tests = loader.loadTestsFromTestCase(klass)
        this_test = tests._tests[0]
        file_suite.addTest(this_test)
        prior_test = this_test

    return file_suite
