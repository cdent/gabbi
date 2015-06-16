#
# Copyright 2014, 2015 Red Hat. All Rights Reserved.
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
"""Test that the driver can build tests effectively.
"""

import os
import unittest

from gabbi import driver

TESTS_DIR = 'test_gabbits'


class DriverTest(unittest.TestCase):

    def setUp(self):
        super(DriverTest, self).setUp()
        self.loader = unittest.defaultTestLoader
        self.test_dir = os.path.join(os.path.dirname(__file__), TESTS_DIR)

    def test_driver_loads_one_test(self):
        suite = driver.build_tests(self.test_dir, self.loader,
                                   host='localhost', port=8001)
        self.assertEqual(1, len(suite._tests),
                         'top level suite contains one suite')
        self.assertEqual(1, len(suite._tests[0]._tests),
                         'contained suite contains one test')
        self.assertEqual('test_driver_single_one',
                         suite._tests[0]._tests[0].__class__.__name__,
                         'test class name maps')

    def test_build_requires_host_or_intercept(self):
        with self.assertRaises(AssertionError):
            driver.build_tests(self.test_dir, self.loader)

    def test_name_key_required(self):
        test_yaml = {'tests': [{'url': '/'}]}

        with self.assertRaises(AssertionError) as failure:
            driver.test_suite_from_yaml(self.loader, 'foo', test_yaml, '.',
                                        'localhost', 80, None, None)
        self.assertEqual('Test name missing in a test in foo.',
                         str(failure.exception))

    def test_url_key_required(self):
        test_yaml = {'tests': [{'name': 'missing url'}]}

        with self.assertRaises(AssertionError) as failure:
            driver.test_suite_from_yaml(self.loader, 'foo', test_yaml, '.',
                                        'localhost', 80, None, None)
        self.assertEqual('Test url missing in test foo_missing_url.',
                         str(failure.exception))

    def test_unsupported_key_errors(self):
        test_yaml = {'tests': [{
            'url': '/',
            'name': 'simple',
            'bad_key': 'wow',
        }]}

        with self.assertRaises(AssertionError) as failure:
            driver.test_suite_from_yaml(self.loader, 'foo', test_yaml, '.',
                                        'localhost', 80, None, None)
        self.assertIn("Invalid test keys used in test foo_simple:",
                      str(failure.exception))
