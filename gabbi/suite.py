# Copyright 2014, 2015 Red Hat
#
# Authors: Chris Dent <chdent@redhat.com>
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

from unittest import suite

from . import fixture


class GabbiSuite(suite.TestSuite):
    """A TestSuite with fixtures.

    The suite wraps the tests with a set of nested context managers that
    operate as fixtures.
    """

    def run(self, result, debug=False):
        """Override TestSuite run to start suite-level fixtures.

        To avoid exception confusion, use a null Fixture when there
        are no fixtures.
        """

        # If there are fixtures, nest in their context.
        fixtures = [fixture.GabbiFixture]
        try:
            fixtures = self._tests[0].fixtures
        except AttributeError:
            pass
        with fixture.nest([fix() for fix in fixtures]):
            result = super(GabbiSuite, self).run(result, debug)

        return result
