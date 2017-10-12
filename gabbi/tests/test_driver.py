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
"""Test that the driver can build tests effectively."""

import os
import unittest

from gabbi import driver


TESTS_DIR = 'test_gabbits'


class DriverTest(unittest.TestCase):

    def setUp(self):
        super(DriverTest, self).setUp()
        self.loader = unittest.defaultTestLoader
        self.test_dir = os.path.join(os.path.dirname(__file__), TESTS_DIR)

    def test_driver_loads_three_tests(self):
        suite = driver.build_tests(self.test_dir, self.loader,
                                   host='localhost', port=8001)
        self.assertEqual(1, len(suite._tests),
                         'top level suite contains one suite')
        self.assertEqual(3, len(suite._tests[0]._tests),
                         'contained suite contains three tests')
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

    def test_build_with_url_provides_host(self):
        """This confirms that url provides the required host."""
        suite = driver.build_tests(self.test_dir, self.loader,
                                   url='https://foo.example.com')
        first_test = suite._tests[0]._tests[0]
        full_url = first_test._parse_url(first_test.test_data['url'])
        ssl = first_test.test_data['ssl']
        self.assertEqual('https://foo.example.com/', full_url)
        self.assertTrue(ssl)

    def test_build_require_ssl(self):
        suite = driver.build_tests(self.test_dir, self.loader,
                                   host='localhost',
                                   require_ssl=True)
        first_test = suite._tests[0]._tests[0]
        full_url = first_test._parse_url(first_test.test_data['url'])
        self.assertEqual('https://localhost:8001/', full_url)

        suite = driver.build_tests(self.test_dir, self.loader,
                                   host='localhost',
                                   require_ssl=False)
        first_test = suite._tests[0]._tests[0]
        full_url = first_test._parse_url(first_test.test_data['url'])
        self.assertEqual('http://localhost:8001/', full_url)

    def test_build_url_target(self):
        suite = driver.build_tests(self.test_dir, self.loader,
                                   host='localhost', port='999',
                                   url='https://example.com:1024/theend')
        first_test = suite._tests[0]._tests[0]
        full_url = first_test._parse_url(first_test.test_data['url'])
        self.assertEqual('https://example.com:1024/theend/', full_url)

    def test_build_url_target_forced_ssl(self):
        suite = driver.build_tests(self.test_dir, self.loader,
                                   host='localhost', port='999',
                                   url='http://example.com:1024/theend',
                                   require_ssl=True)
        first_test = suite._tests[0]._tests[0]
        full_url = first_test._parse_url(first_test.test_data['url'])
        self.assertEqual('https://example.com:1024/theend/', full_url)

    def test_build_url_use_prior_test(self):
        suite = driver.build_tests(self.test_dir, self.loader,
                                   host='localhost',
                                   use_prior_test=True)
        for test in suite._tests[0]._tests:
            if test.test_data['name'] != 'use_prior_false':
                expected_use_prior = True
            else:
                expected_use_prior = False

            self.assertEqual(expected_use_prior,
                             test.test_data['use_prior_test'])

        suite = driver.build_tests(self.test_dir, self.loader,
                                   host='localhost',
                                   use_prior_test=False)
        for test in suite._tests[0]._tests:
            self.assertEqual(False, test.test_data['use_prior_test'])
