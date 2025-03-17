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
"""A TestSuite for containing gabbi tests.

This suite has two features: the contained tests are ordered and there
are suite-level fixtures that operate as context managers.
"""

import sys
import unittest

from gabbi import fixture


def noop(*args):
    """A noop method used to disable collected tests."""
    pass


class GabbiSuite(unittest.TestSuite):
    """A TestSuite with fixtures.

    The suite wraps the tests with a set of nested context managers that
    operate as fixtures.

    If a fixture raises unittest.case.SkipTest during setup, all the
    tests in this suite will be skipped.
    """

    def run(self, result, debug=False):
        """Override TestSuite run to start suite-level fixtures.

        To avoid exception confusion, use a null Fixture when there
        are no fixtures.
        """

        fixtures, host, port = self._get_fixtures()

        try:
            with fixture.nest([fix() for fix in fixtures]):
                result = super(GabbiSuite, self).run(result, debug)
        except unittest.SkipTest as exc:
            for test in self._tests:
                result.addSkip(test, str(exc))
        # If we have an exception in the nested fixtures, that means
        # there's been an exception somewhere in the cycle other
        # than a specific test (as that would have been caught
        # already), thus from a fixture. If that exception were to
        # continue to raise here, then some test runners would
        # swallow it and the traceback of the failure would be
        # undiscoverable. To ensure the traceback is reported (via
        # the testrunner) to a human, the first test in the suite is
        # marked as having an error (it's fixture failed) and then
        # the entire suite is skipped, and the result stream told
        # we're done. If there are no tests (an empty suite) the
        # exception is re-raised.
        except Exception:
            if self._tests:
                result.addError(self._tests[0], sys.exc_info())
                for test in self._tests:
                    result.addSkip(test, 'fixture failure')
                result.stop()
            else:
                raise

        return result

    def start(self, result, tests=None):
        """Start fixtures when using pytest."""
        tests = tests or []
        fixtures, host, port = self._get_fixtures()

        self.used_fixtures = []
        try:
            for fix in fixtures:
                fix_object = fix()
                fix_object.__enter__()
                self.used_fixtures.append(fix_object)
        except unittest.SkipTest as exc:
            # Disable the already collected tests that we now wish
            # to skip.
            for test in tests:
                test.run = noop
                test.add_marker('skip')
            result.addSkip(self, str(exc))

    def stop(self):
        """Stop fixtures when using pytest."""
        for fix in reversed(self.used_fixtures):
            fix.__exit__(None, None, None)

    def _get_fixtures(self):
        fixtures = [fixture.GabbiFixture]
        host = port = None
        try:
            first_test = self._find_first_full_test()
            fixtures = first_test.fixtures
            host = first_test.host
            port = first_test.port

        except AttributeError:
            pass

        return fixtures, host, port

    def _find_first_full_test(self):
        """Traverse a sparse test suite to find the first HTTPTestCase.

        When only some tests are requested empty TestSuites replace the
        unrequested tests.
        """
        for test in self._tests:
            if hasattr(test, 'fixtures'):
                return test
        raise AttributeError('no fixtures found')
