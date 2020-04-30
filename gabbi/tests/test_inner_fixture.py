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
"""Test the works of inner and outer fixtures.

An "outer" fixture runs once per test suite. An "inner" is per test request.
"""

import os
import sys

from gabbi import driver
# TODO(cdent): test_pytest allows pytest to see the tests this module
# produces. Without it, the generator will not run. It is a todo because
# needing to do this is annoying and gross.
from gabbi.driver import test_pytest  # noqa
from gabbi import fixture
from gabbi.tests import simple_wsgi


TESTS_DIR = 'gabbits_inner'
COUNT_INNER = 0
COUNT_OUTER = 0


class OuterFixture(fixture.GabbiFixture):
    """Assert an outer fixture is only started once and is stopped."""

    def start_fixture(self):
        global COUNT_OUTER
        COUNT_OUTER += 1

    def stop_fixture(self):
        assert COUNT_OUTER == 1


class InnerFixture(object):
    """Test that setUp is called 3 times."""

    def setUp(self):
        global COUNT_INNER
        COUNT_INNER += 1

    def cleanUp(self):
        assert 1 <= COUNT_INNER <= 3


BUILD_TEST_ARGS = dict(
    intercept=simple_wsgi.SimpleWsgi,
    fixture_module=sys.modules[__name__],
    inner_fixtures=[InnerFixture],
)


def load_tests(loader, tests, pattern):
    test_dir = os.path.join(os.path.dirname(__file__), TESTS_DIR)
    return driver.build_tests(test_dir, loader,
                              test_loader_name=__name__,
                              **BUILD_TEST_ARGS)


def pytest_generate_tests(metafunc):
    test_dir = os.path.join(os.path.dirname(__file__), TESTS_DIR)
    driver.py_test_generator(test_dir, metafunc=metafunc,
                             **BUILD_TEST_ARGS)
