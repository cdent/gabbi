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

"""A sample test module to exercise the code.

For the sake of exploratory development.
"""


import os
import sys


from gabbi import driver
from gabbi import fixture
from gabbi import handlers
from gabbi import simple_wsgi

TESTS_DIR = 'gabbits_intercept'


class TestFixtureOne(fixture.GabbiFixture):
    """Drive the fixture testing weakly."""
    pass


class TestFixtureTwo(fixture.GabbiFixture):
    """Drive the fixture testing weakly."""
    pass


class TestResponseHandler(handlers.ResponseHandler):
    """A sample response handler just to test."""

    test_key_suffix = 'test'
    test_key_value = []

    def preprocess(self, test):
        """Add some data if the data is a string."""
        try:
            test.output = test.output + '\nAnother line'
        except TypeError:
            pass

    def action(self, test, expected, value=None):
        expected = expected.replace('COW', '', 1)
        test.assertIn(expected, test.output)


# Incorporate the SkipAllFixture into this namespace so it can be used
# by tests (cf. skipall.yaml).
SkipAllFixture = fixture.SkipAllFixture


def load_tests(loader, tests, pattern):
    """Provide a TestSuite to the discovery process."""
    # Set and environment variable for one of the tests.
    os.environ['GABBI_TEST_URL'] = 'takingnames'
    prefix = os.environ.get('GABBI_PREFIX')
    test_dir = os.path.join(os.path.dirname(__file__), TESTS_DIR)
    return driver.build_tests(test_dir, loader, host=None,
                              intercept=simple_wsgi.SimpleWsgi,
                              prefix=prefix,
                              fixture_module=sys.modules[__name__],
                              response_handlers=[TestResponseHandler])
