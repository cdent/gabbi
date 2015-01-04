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

"""Manage fixtures for gabbi at the test suite level."""

import sys
from contextlib import contextmanager

import six


class GabbiFixtureError(Exception):
    """Generic exception for GabbiFixture."""
    pass


class GabbiFixture(object):
    """A context manager that operates as a fixture.

    Subclasses must implement start_fixture and stop_fixture, each of which
    contain the logic for stopping and starting whatever the fixture is.
    What a fixture is is left as an exercise for the implementor.

    These context managers will be nested so any actually work needs to
    happen in `start_fixture` and `stop_fixture` and not in ``__init__``.
    Otherwise exception handling will not work properly.
    """

    def __enter__(self):
        self.start_fixture()

    def __exit__(self, type, value, traceback):
        self.stop_fixture()

    def start_fixture(self):
        """Implement the actual workings of starting the fixture here."""
        pass

    def stop_fixture(self):
        """Implement the actual workings of stopping the fixture here."""
        pass


@contextmanager
def nest(fixtures):
    """Nest a series of fixtures."""
    vars = []
    exits = []
    exc = (None, None, None)
    try:
        for fixture in fixtures:
            enter = fixture.__enter__
            exit = fixture.__exit__
            vars.append(enter())
            exits.append(exit)
        yield vars
    except:
        exc = sys.exc_info()
    finally:
        while exits:
            exit = exits.pop()
            try:
                if exit(*exc):
                    exc = (None, None, None)
            except:
                exc = sys.exc_info()
        if exc != (None, None, None):
            six.reraise(exc[0], exc[1], exc[2])
