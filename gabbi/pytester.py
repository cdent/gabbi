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
"""A pytest plugin that runs under the covers with gabbi.

This is a backwards compatible improvement to the way gabbi can work with
pytest. Tests are loaded (and yielded in the same way) but they are filtered
more correctly, and fixture start and stops are done more correctly.

This allows the test count to be accurate, which is nice.
"""

import pytest


# Globals storing the test-like functions to be used when starting
# and stopping a suite.
STARTS = {}
STOPS = {}


def get_cleanname(item):
    """Extract a test name from a pytest Function item."""
    if '[' in item.name:
        cleanname = item.name.split('[', 1)[1]
        cleanname = cleanname.split(']', 1)[0]
        return cleanname
    return item.name


def get_suitename(name):
    """Extract a test suite from a clean name.

    This is fragile. It assumes there are no underscores in
    suite names, which is not always true.
    """
    if name.startswith('start_') or name.startswith('stop_'):
        _, name = name.split('_', 1)
    return name.split('_', 2)[1]


def c_pytest_collection_modifyitems(items, config):
    """Set the starters and stoppers for a limited collection of tests."""
    latest_suite = None
    latest_item = None
    for item in items:
        cleanname = get_cleanname(item)
        if not cleanname.startswith(
                ('stop_driver_', 'start_driver_', 'driver_')):
            continue
        prefix, testname = cleanname.split('_', 1)
        suitename, _ = testname.split('_', 1)
        if prefix == 'start' or prefix == 'stop':
            continue
        if latest_suite != suitename:
            item.starter = STARTS[suitename]
            if latest_item:
                latest_item.stopper = STOPS[
                    get_suitename(get_cleanname(latest_item))]
        latest_suite = suitename
        latest_item = item
    # Set the last stopper in the list
    if latest_item:
        latest_item.stopper = STOPS[get_suitename(get_cleanname(latest_item))]


def a_pytest_collection_modifyitems(items, config):
    """Traverse collected tests to save START and STOPS.

    Remove those START and STOPS from the tests to run.
    """
    remaining = []
    deselected = []
    for item in items:
        cleanname = get_cleanname(item)
        if not cleanname.startswith(
                ('stop_driver_', 'start_driver_', 'driver_')):
            remaining.append(item)
            continue
        suitename = get_suitename(cleanname)
        if cleanname.startswith('start_'):
            test = item.callspec.params['test']
            result = item.callspec.params['result']
            STARTS[suitename] = (test, result)
            deselected.append(item)
        elif cleanname.startswith('stop_'):
            test = item.callspec.params['test']
            STOPS[suitename] = test
            deselected.append(item)
        else:
            remaining.append(item)

    if deselected:
        items[:] = remaining


@pytest.hookimpl(hookwrapper=True)
def pytest_collection_modifyitems(items, config):
    """Hook for processing collected tests.

    Discover start and stops, then use the default hook
    for filter for keywords and markers, then attach
    starter and stopper to the remaining tests.
    """
    a_pytest_collection_modifyitems(items, config)
    yield
    c_pytest_collection_modifyitems(items, config)


def pytest_runtest_setup(item):
    """Run a starter if a test has one.

    This is done before run, so it means that a single test will
    run its priors after running this.
    """
    if hasattr(item, 'starter'):
        test, result = item.starter
        test(result)


def pytest_runtest_teardown(item, nextitem):
    """Run a stopper if a test has one."""
    if hasattr(item, 'stopper'):
        item.stopper()
