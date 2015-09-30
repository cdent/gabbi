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

"""Manage fixtures for gabbi at the test suite level."""

import contextlib
import sys
from unittest import case

import six
import wsgi_intercept
from wsgi_intercept import httplib2_intercept


class GabbiFixtureError(Exception):
    """Generic exception for GabbiFixture."""
    pass


class GabbiFixture(object):
    """A context manager that operates as a fixture.

    Subclasses must implement ``start_fixture`` and ``stop_fixture``, each
    of which contain the logic for stopping and starting whatever the
    fixture is. What a fixture is is left as an exercise for the implementor.

    These context managers will be nested so any actual work needs to
    happen in ``start_fixture`` and ``stop_fixture`` and not in ``__init__``.
    Otherwise exception handling will not work properly.
    """

    def __init__(self):
        self.exc_type = None
        self.exc_value = None
        self.traceback = None

    def __enter__(self):
        self.start_fixture()

    def __exit__(self, exc_type, value, traceback):
        self.exc_type = exc_type
        self.exc_value = value
        self.traceback = traceback
        self.stop_fixture()

    def start_fixture(self):
        """Implement the actual workings of starting the fixture here."""
        pass

    def stop_fixture(self):
        """Implement the actual workings of stopping the fixture here."""
        pass


class InterceptFixture(GabbiFixture):
    """Start up the wsgi intercept. This should not be called directly."""

    httplib2_intercept.install()

    def __init__(self, host, port, app, prefix):
        super(InterceptFixture, self).__init__()
        self.host = host
        self.port = int(port)
        self.app = app
        self.script_name = prefix or ''

    def start_fixture(self):
        wsgi_intercept.add_wsgi_intercept(self.host, self.port, self.app,
                                          script_name=self.script_name)

    def stop_fixture(self):
        wsgi_intercept.remove_wsgi_intercept(self.host, self.port)


class SkipAllFixture(GabbiFixture):
    """A fixture that skips all the tests in the current suite."""

    def start_fixture(self):
        raise case.SkipTest('entire suite skipped')


@contextlib.contextmanager
def nest(fixtures):
    """Nest a series of fixtures.

    This is duplicated from ``nested`` in the stdlib, which has been
    deprecated because of issues with how exceptions are difficult to
    handle during ``__init__``. Gabbi needs to nest an unknown number
    of fixtures dynamically, so the ``with`` syntax that replaces
    ``nested`` will not work.
    """
    contexts = []
    exits = []
    exc = (None, None, None)
    try:
        for fixture in fixtures:
            enter_func = fixture.__enter__
            exit_func = fixture.__exit__
            contexts.append(enter_func())
            exits.append(exit_func)
        yield contexts
    except Exception:
        exc = sys.exc_info()
    finally:
        while exits:
            exit_func = exits.pop()
            try:
                if exit_func(*exc):
                    exc = (None, None, None)
            except Exception:
                exc = sys.exc_info()
        if exc != (None, None, None):
            six.reraise(exc[0], exc[1], exc[2])
