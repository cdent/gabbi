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

    def test_driver_loads_two_tests(self):
        suite = driver.build_tests(self.test_dir, self.loader,
                                   host='localhost', port=8001)
        self.assertEqual(1, len(suite._tests),
                         'top level suite contains one suite')
        self.assertEqual(2, len(suite._tests[0]._tests),
                         'contained suite contains two tests')
        the_one_test = suite._tests[0]._tests[0]
        self.assertEqual('test_driver_sample_one',
                         the_one_test.__class__.__name__,
                         'test class name maps')
        self.assertEqual('one',
                         the_one_test.test_data['name'])
        self.assertEqual('/', the_one_test.test_data['url'])

    def test_driver_prefix(self):
        suite = driver.build_tests(self.test_dir, self.loader,
                                   host='localhost', port=8001,
                                   prefix='/mountpoint')
        the_one_test = suite._tests[0]._tests[0]
        the_two_test = suite._tests[0]._tests[1]
        self.assertEqual('/mountpoint', the_one_test.prefix)
        self.assertEqual('/mountpoint', the_two_test.prefix)

    def test_build_requires_host_or_intercept(self):
        with self.assertRaises(AssertionError):
            driver.build_tests(self.test_dir, self.loader)

    def test_tests_key_required(self):
        test_yaml = {'name': 'house', 'url': '/'}

        with self.assertRaises(driver.GabbiFormatError) as failure:
            driver.test_suite_from_yaml(self.loader, 'foo', test_yaml, '.',
                                        'localhost', 80, None, None)
        self.assertEqual('malformed test file, "tests" key required',
                         str(failure.exception))

    def test_upper_dict_required(self):
        test_yaml = [{'name': 'house', 'url': '/'}]
        with self.assertRaises(driver.GabbiFormatError) as failure:
            driver.test_suite_from_yaml(self.loader, 'foo', test_yaml, '.',
                                        'localhost', 80, None, None)
        self.assertEqual('malformed test file, invalid format',
                         str(failure.exception))

    def test_inner_list_required(self):
        test_yaml = {'tests': {'name': 'house', 'url': '/'}}
        with self.assertRaises(driver.GabbiFormatError) as failure:
            driver.test_suite_from_yaml(self.loader, 'foo', test_yaml, '.',
                                        'localhost', 80, None, None)
        self.assertIn('test chunk is not a dict at',
                      str(failure.exception))

    def test_name_key_required(self):
        test_yaml = {'tests': [{'url': '/'}]}

        with self.assertRaises(driver.GabbiFormatError) as failure:
            driver.test_suite_from_yaml(self.loader, 'foo', test_yaml, '.',
                                        'localhost', 80, None, None)
        self.assertEqual('Test name missing in a test in foo.',
                         str(failure.exception))

    def test_url_key_required(self):
        test_yaml = {'tests': [{'name': 'missing url'}]}

        with self.assertRaises(driver.GabbiFormatError) as failure:
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

        with self.assertRaises(driver.GabbiFormatError) as failure:
            driver.test_suite_from_yaml(self.loader, 'foo', test_yaml, '.',
                                        'localhost', 80, None, None)
        self.assertIn("Invalid test keys used in test foo_simple:",
                      str(failure.exception))

    def test_method_url_pair_format_error(self):
        test_yaml = {'defaults': {'GET': '/foo'}, 'tests': []}
        with self.assertRaises(driver.GabbiFormatError) as failure:
            driver.test_suite_from_yaml(self.loader, 'foo', test_yaml, '.',
                                        'localhost', 80, None, None)
        self.assertIn('"METHOD: url" pairs not allowed in defaults',
                      str(failure.exception))

    def test_method_url_pair_duplication_format_error(self):
        test_yaml = {'tests': [{
            'GET': '/',
            'POST': '/',
            'name': 'duplicate methods',
        }]}
        with self.assertRaises(driver.GabbiFormatError) as failure:
            driver.test_suite_from_yaml(self.loader, 'foo', test_yaml, '.',
                                        'localhost', 80, None, None)
        self.assertIn(
            'duplicate method/URL directive in "foo_duplicate_methods"',
            str(failure.exception)
        )

    def test_dict_on_invalid_key(self):
        test_yaml = {'tests': [{
            'name': '...',
            'GET': '/',
            'response_html': {
                'foo': 'hello',
                'bar': 'world',
            }
        }]}

        with self.assertRaises(driver.GabbiFormatError) as failure:
            driver.test_suite_from_yaml(self.loader, 'foo', test_yaml, '.',
                                        'localhost', 80, None, None)
        self.assertIn(
            "invalid key in test: 'response_html'",
            str(failure.exception)
        )
