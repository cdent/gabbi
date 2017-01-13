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
"""Unit tests for the gabbi.suite.
"""

import sys
import unittest

from gabbi import fixture
from gabbi import suitemaker

VALUE_ERROR = 'value error sentinel'


class FakeFixture(fixture.GabbiFixture):

    def start_fixture(self):
        raise ValueError(VALUE_ERROR)


class SuiteTest(unittest.TestCase):

    def test_suite_catches_fixture_fail(self):
        """When a fixture fails in start_fixture it should fail
        the first test in the suite and skip the others.
        """
        loader = unittest.defaultTestLoader
        result = unittest.TestResult()
        test_data = {'fixtures': ['FakeFixture'],
                     'tests': [{'name': 'alpha', 'GET': '/'},
                               {'name': 'beta', 'GET': '/'}]}
        test_suite = suitemaker.test_suite_from_dict(
            loader, 'foo', test_data, '.', 'localhost',
            80, sys.modules[__name__], None)

        test_suite.run(result)

        self.assertEqual(2, len(result.skipped))
        self.assertEqual(1, len(result.errors))

        errored_test, trace = result.errors[0]

        self.assertIn('foo_alpha', str(errored_test))
        self.assertIn(VALUE_ERROR, trace)
