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
"""Test pytest driving of tests.

Unittest loaders don't see this file and pytest doesn't see load_tests,
so we manage to get coverage across both types of drivers, from tox,
without duplication.
"""

import os

from gabbi import driver
from gabbi.tests import simple_wsgi
from gabbi.tests import test_intercept

TESTS_DIR = 'gabbits_intercept'


def test_from_build():

    os.environ['GABBI_TEST_URL'] = 'takingnames'
    test_dir = os.path.join(os.path.dirname(__file__), TESTS_DIR)
    test_generator = driver.py_test_generator(
        test_dir, intercept=simple_wsgi.SimpleWsgi,
        fixture_module=test_intercept,
        response_handlers=[test_intercept.TestResponseHandler])

    # TODO(cdent): Where is our Python3!
    # yield from test_generator
    for test in test_generator:
        yield test
