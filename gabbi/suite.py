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

import unittest

from wsgi_intercept import interceptor

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

        fixtures, intercept, host, port, prefix = self._get_intercept()

        try:
            with fixture.nest([fix() for fix in fixtures]):
                if intercept:
                    with interceptor.Urllib3Interceptor(
                            intercept, host, port, prefix):
                        result = super(GabbiSuite, self).run(result, debug)
                else:
                    result = super(GabbiSuite, self).run(result, debug)
        except unittest.SkipTest as exc:
            for test in self._tests:
                result.addSkip(test, str(exc))

        return result

    def start(self, result):
        """Start fixtures when using pytest."""
        fixtures, intercept, host, port, prefix = self._get_intercept()

        self.used_fixtures = []
        try:
            for fix in fixtures:
                fix_object = fix()
                fix_object.__enter__()
                self.used_fixtures.append(fix_object)
        except unittest.SkipTest as exc:
            # Disable the already collected tests that we now wish
            # to skip.
            for test in self:
                test.run = noop
                result.addSkip(test, str(exc))
            result.addSkip(self, str(exc))
        if intercept:
            intercept_fixture = interceptor.Urllib3Interceptor(
                intercept, host, port, prefix)
            intercept_fixture.__enter__()
            self.used_fixtures.append(intercept_fixture)

    def stop(self):
        """Stop fixtures when using pytest."""
        for fix in reversed(self.used_fixtures):
            fix.__exit__(None, None, None)

    def _get_intercept(self):
        fixtures = [fixture.GabbiFixture]
        intercept = host = port = prefix = None
        try:
            first_test = self._find_first_full_test()
            fixtures = first_test.fixtures
            host = first_test.host
            port = first_test.port
            prefix = first_test.prefix
            intercept = first_test.intercept

            # Unbind a passed in WSGI application. During the
            # metaclass building process intercept becomes bound.
            try:
                intercept = intercept.__func__
            except AttributeError:
                pass
        except AttributeError:
            pass

        return fixtures, intercept, host, port, prefix

    def _find_first_full_test(self):
        """Traverse a sparse test suite to find the first HTTPTestCase.

        When only some tests are requested empty TestSuites replace the
        unrequested tests.
        """
        for test in self._tests:
            if hasattr(test, 'fixtures'):
                return test
        raise AttributeError('no fixtures found')
