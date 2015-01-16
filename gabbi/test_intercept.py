#
# Copyright 2014, 2015 Red Hat. All Rights Reserved.
#
# Author: Chris Dent <chdent@redhat.com>
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
from gabbi import simple_wsgi


TESTS_DIR = 'gabbits_intercept'


class TestFixtureOne(fixture.GabbiFixture):
    """Drive the fixture testing weakly."""
    pass


class TestFixtureTwo(fixture.GabbiFixture):
    """Drive the fixture testing weakly."""
    pass


def load_tests(loader, tests, pattern):
    """Provide a TestSuite to the discovery process."""
    test_dir = os.path.join(os.path.dirname(__file__), TESTS_DIR)
    return driver.build_tests(test_dir, loader, host=None,
                              intercept=simple_wsgi.SimpleWsgi,
                              fixture_module=sys.modules[__name__])
