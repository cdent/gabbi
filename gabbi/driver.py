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
"""Generate HTTP tests from YAML files

Each HTTP request is its own TestCase and can be requested to be run in
isolation from other tests. If it is a member of a sequence of requests,
prior requests will be run.

A sequence is represented by an ordered list in a single YAML file.

Each sequence becomes a TestSuite.

An entire directory of YAML files is a TestSuite of TestSuites.
"""

import glob
import inspect
import os
import unittest
from unittest import suite
import uuid
import warnings

from gabbi import case
from gabbi import exception
from gabbi import handlers
from gabbi import reporter
from gabbi import suitemaker
from gabbi import utils


def build_tests(path, loader, host=None, port=8001, intercept=None,
                test_loader_name=None, fixture_module=None,
                response_handlers=None, prefix='', require_ssl=False,
                url=None):
    """Read YAML files from a directory to create tests.

    Each YAML file represents an ordered sequence of HTTP requests.

    :param path: The directory where yaml files are located.
    :param loader: The TestLoader.
    :param host: The host to test against. Do not use with ``intercept``.
    :param port: The port to test against. Used with ``host``.
    :param intercept: WSGI app factory for wsgi-intercept.
    :param test_loader_name: Base name for test classes. Rarely used.
    :param fixture_module: Python module containing fixture classes.
    :param response_handers: :class:`~gabbi.handlers.ResponseHandler` classes.
    :type response_handlers: List of ResponseHandler classes.
    :param prefix: A URL prefix for all URLs that are not fully qualified.
    :param url: A full URL to test against. Replaces host, port and prefix.
    :param require_ssl: If ``True``, make all tests default to using SSL.
    :rtype: TestSuite containing multiple TestSuites (one for each YAML file).
    """

    # Exit immediately if we have no host to access, either via a real host
    # or an intercept.
    if not bool(host) ^ bool(intercept):
        raise AssertionError('must specify exactly one of host or intercept')

    # If url is being used, reset host, port and prefix.
    if url:
        host, port, prefix, force_ssl = utils.host_info_from_target(url)
        if force_ssl and not require_ssl:
            require_ssl = force_ssl

    if test_loader_name is None:
        test_loader_name = inspect.stack()[1]
        test_loader_name = os.path.splitext(os.path.basename(
            test_loader_name[1]))[0]

    # Initialize response handlers.
    response_handlers = response_handlers or []
    for handler in handlers.RESPONSE_HANDLERS + response_handlers:
        handler(case.HTTPTestCase)

    top_suite = suite.TestSuite()
    for test_file in glob.iglob('%s/*.yaml' % path):
        if '_' in os.path.basename(test_file):
            warnings.warn(exception.GabbiSyntaxWarning(
                "'_' in test filename %s. This can break suite grouping."
                % test_file))
        if intercept:
            host = str(uuid.uuid4())
        suite_dict = utils.load_yaml(yaml_file=test_file)
        test_base_name = '%s_%s' % (
            test_loader_name, os.path.splitext(os.path.basename(test_file))[0])

        if require_ssl:
            if 'defaults' in suite_dict:
                suite_dict['defaults']['ssl'] = True
            else:
                suite_dict['defaults'] = {'ssl': True}

        file_suite = suitemaker.test_suite_from_dict(
            loader, test_base_name, suite_dict, path, host, port,
            fixture_module, intercept, prefix)
        top_suite.addTest(file_suite)
    return top_suite


def py_test_generator(test_dir, host=None, port=8001, intercept=None,
                      prefix=None, test_loader_name=None,
                      fixture_module=None, response_handlers=None,
                      require_ssl=False, url=None):
    """Generate tests cases for py.test

    This uses build_tests to create TestCases and then yields them in
    a way that pytest can handle.
    """

    import pytest
    pluginmanager = pytest.config.pluginmanager
    pluginmanager.import_plugin('gabbi.pytester')

    loader = unittest.TestLoader()
    result = reporter.PyTestResult()
    tests = build_tests(test_dir, loader, host=host, port=port,
                        intercept=intercept,
                        test_loader_name=test_loader_name,
                        fixture_module=fixture_module,
                        response_handlers=response_handlers,
                        prefix=prefix, require_ssl=require_ssl,
                        url=url)

    for test in tests:
        if hasattr(test, '_tests'):
            # Establish fixtures as if they were tests. These will
            # be cleaned up by the pytester plugin.
            yield 'start_%s' % test._tests[0].__class__.__name__, \
                test.start, result
            for subtest in test:
                yield '%s' % subtest.__class__.__name__, subtest, result
            yield 'stop_%s' % test._tests[0].__class__.__name__, test.stop


def test_suite_from_yaml(loader, test_base_name, test_yaml, test_directory,
                         host, port, fixture_module, intercept, prefix=''):
    """Legacy wrapper retained for backwards compatibility."""

    with warnings.catch_warnings():  # ensures warnings filter is restored
        warnings.simplefilter('default', DeprecationWarning)
        warnings.warn('test_suite_from_yaml has been renamed to '
                      'test_suite_from_dict', DeprecationWarning, stacklevel=2)
    return suitemaker.test_suite_from_dict(
        loader, test_base_name, test_yaml, test_directory, host, port,
        fixture_module, intercept, prefix)
