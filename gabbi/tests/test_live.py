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

"""A test module to exercise the live requests functionality"""


import os
import sys
from unittest import case

from gabbi import driver
# TODO(cdent): test_pytest allows pytest to see the tests this module
# produces. Without it, the generator will not run. It is a todo because
# needing to do this is annoying and gross.
from gabbi.driver import test_pytest  # noqa
from gabbi import fixture


TESTS_DIR = 'gabbits_live'


class LiveSkipFixture(fixture.GabbiFixture):
    """Skip a test file when we don't want to use the internet."""

    def start_fixture(self):
        if os.environ.get('GABBI_SKIP_NETWORK', 'False').lower() == 'true':
            raise case.SkipTest('live tests skipped')


BUILD_TEST_ARGS = dict(
    host='google.com',
    fixture_module=sys.modules[__name__],
    port=443
)


def load_tests(loader, tests, pattern):
    """Provide a TestSuite to the discovery process."""
    test_dir = os.path.join(os.path.dirname(__file__), TESTS_DIR)
    return driver.build_tests(test_dir, loader, **BUILD_TEST_ARGS)


def pytest_generate_tests(metafunc):
    test_dir = os.path.join(os.path.dirname(__file__), TESTS_DIR)
    driver.py_test_generator(test_dir, metafunc=metafunc, **BUILD_TEST_ARGS)
