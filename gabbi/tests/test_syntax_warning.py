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
"""Test that the driver warns on bad yaml name."""

import os
import unittest
import warnings

from gabbi import driver
from gabbi import exception


TESTS_DIR = 'warning_gabbits'


class DriverTest(unittest.TestCase):

    def setUp(self):
        super(DriverTest, self).setUp()
        self.loader = unittest.defaultTestLoader
        self.test_dir = os.path.join(os.path.dirname(__file__), TESTS_DIR)

    def test_driver_warnings_on_files(self):
        with warnings.catch_warnings(record=True) as the_warnings:
            driver.build_tests(
                self.test_dir, self.loader, host='localhost', port=8001)
            self.assertEqual(1, len(the_warnings))
            the_warning = the_warnings[-1]
            self.assertEqual(
                the_warning.category, exception.GabbiSyntaxWarning)
            self.assertIn("'_' in test filename", str(the_warning.message))
