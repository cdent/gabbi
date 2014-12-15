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
import os
from unittest import suite

import testtools
import yaml


def load_yaml(yaml_file):
    """Read and parse any YAML file. Let exceptions flow where they may.
    """
    with open(yaml_file) as source:
        return yaml.safe_load(source.read())


class Builder(type):

    def __new__(mcs, name, bases, d):
        return type.__new__(mcs, name, bases, d)


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
        if self.has_run:
            return
        if self.prior and not self.prior.has_run:
            self.prior.run()
        self.assertTrue(self.test_data['url'])


def build_tests(path, loader, tests, pattern):
    """Read YAML files from a directory to create tests.

    Each YAML file represents an ordered sequence of HTTP requests.
    """
    top_suite = suite.TestSuite()

    path = '%s/*.yaml' % path

    for test_file in glob.iglob(path):
        file_suite = suite.TestSuite()
        test_data = load_yaml(test_file)
        test_base_name = os.path.splitext(os.path.basename(test_file))[0]

        prior_test = None
        for test in test_data:
            test_name = '%s_%s' % (test_base_name,
                                   test['name'].lower().replace(' ', '_'))
            # Use metaclasses to build a class of the necessary type
            # with relevant arguments.
            klass = Builder(test_name, (HTTPTestCase,),
                            {'test_data': test,
                             'prior': prior_test,
                             'has_run': False})

            tests = loader.loadTestsFromTestCase(klass)
            this_test = tests._tests[0]
            file_suite.addTest(this_test)
            prior_test = this_test

        top_suite.addTest(file_suite)

    return top_suite
