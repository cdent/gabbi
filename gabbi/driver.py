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

from gabbi import exception
from gabbi import handlers
from gabbi import reporter
from gabbi import suitemaker
from gabbi import utils


def build_tests(path, loader, host=None, port=8001, intercept=None,
                test_loader_name=None, fixture_module=None,
                response_handlers=None, content_handlers=None,
                prefix='', require_ssl=False, cert_validate=True, url=None,
                inner_fixtures=None, verbose=False,
                use_prior_test=True, safe_yaml=True):
    """Read YAML files from a directory to create tests.

    Each YAML file represents a list of HTTP requests.

    :param path: The directory where yaml files are located.
    :param loader: The TestLoader.
    :param host: The host to test against. Do not use with ``intercept``.
    :param port: The port to test against. Used with ``host``.
    :param intercept: WSGI app factory for wsgi-intercept.
    :param test_loader_name: Base name for test classes. Use this to align the
                             naming of the tests with other tests in a system.
    :param fixture_module: Python module containing fixture classes.
    :param response_handers: :class:`~gabbi.handlers.ResponseHandler` classes.
    :type response_handlers: List of ResponseHandler classes.
    :param content_handlers: ContentHandler classes.
    :type content_handlers: List of ContentHandler classes.
    :param prefix: A URL prefix for all URLs that are not fully qualified.
    :param url: A full URL to test against. Replaces host, port and prefix.
    :param require_ssl: If ``True``, make all tests default to using SSL.
    :param inner_fixtures: A list of ``Fixtures`` to use with each
                           individual test request.
    :type inner_fixtures: List of classes with setUp and cleanUp methods to
                          be used as fixtures.
    :param verbose: If ``True`` or ``'all'``, make tests verbose by default
                    ``'headers'`` and ``'body'`` are also accepted.
    :param use_prior_test: If ``True``, uses prior test to create ordered
                           sequence of tests
    :param safe_yaml: If ``True``, recognizes only standard YAML tags and not
                      Python object
    :param cert_validate: If ``False`` ssl server certificate will be ignored,
                        further it will not be validated if provided
                        (set cert_reqs=CERT_NONE to the Http object)
    :rtype: TestSuite containing multiple TestSuites (one for each YAML file).
    """

    # If url is being used, reset host, port and prefix.
    if url:
        host, port, prefix, force_ssl = utils.host_info_from_target(url)
        if force_ssl and not require_ssl:
            require_ssl = force_ssl

    # Exit immediately if we have no host to access, either via a real host
    # or an intercept.
    if not ((host is not None) ^ bool(intercept)):
        raise AssertionError(
            'must specify exactly one of host or url, or intercept')

    # If the client has not provided a name to use as our base,
    # create one so that tests are effectively namespaced.
    if test_loader_name is None:
        all_test_base_name = inspect.stack()[1]
        all_test_base_name = os.path.splitext(
            os.path.basename(all_test_base_name[1]))[0]
    else:
        all_test_base_name = None

    # Initialize response and content handlers. This is effectively
    # duplication of effort but not results. This allows for
    # backwards compatibility for existing callers.
    response_handlers = response_handlers or []
    content_handlers = content_handlers or []
    handler_objects = []
    for handler in (content_handlers + response_handlers +
                    handlers.RESPONSE_HANDLERS):
        handler_objects.append(handler())

    top_suite = suite.TestSuite()
    for test_file in glob.iglob('%s/*.yaml' % path):
        if '_' in os.path.basename(test_file):
            warnings.warn(exception.GabbiSyntaxWarning(
                "'_' in test filename %s. This can break suite grouping."
                % test_file))
        if intercept:
            host = str(uuid.uuid4())
        suite_dict = utils.load_yaml(yaml_file=test_file,
                                     safe=safe_yaml)
        test_base_name = os.path.splitext(os.path.basename(test_file))[0]
        if all_test_base_name:
            test_base_name = '%s_%s' % (all_test_base_name, test_base_name)

        if require_ssl:
            if 'defaults' in suite_dict:
                suite_dict['defaults']['ssl'] = True
            else:
                suite_dict['defaults'] = {'ssl': True}

        if any((verbose == opt for opt in [True, 'all', 'headers', 'body'])):
            if 'defaults' in suite_dict:
                suite_dict['defaults']['verbose'] = verbose
            else:
                suite_dict['defaults'] = {'verbose': verbose}

        if not cert_validate:
            if 'defaults' in suite_dict:
                suite_dict['defaults']['cert_validate'] = False
            else:
                suite_dict['defaults'] = {'cert_validate': False}

        if not use_prior_test:
            if 'defaults' in suite_dict:
                suite_dict['defaults']['use_prior_test'] = use_prior_test
            else:
                suite_dict['defaults'] = {'use_prior_test': use_prior_test}

        file_suite = suitemaker.test_suite_from_dict(
            loader, test_base_name, suite_dict, path, host, port,
            fixture_module, intercept, prefix=prefix,
            test_loader_name=test_loader_name, handlers=handler_objects,
            inner_fixtures=inner_fixtures)
        top_suite.addTest(file_suite)
    return top_suite


def py_test_generator(test_dir, host=None, port=8001, intercept=None,
                      prefix=None, test_loader_name=None,
                      fixture_module=None, response_handlers=None,
                      content_handlers=None, require_ssl=False, url=None,
                      metafunc=None, use_prior_test=True,
                      inner_fixtures=None, safe_yaml=True, cert_validate=True):
    """Generate tests cases for py.test

    This uses build_tests to create TestCases and then yields them in
    a way that pytest can handle.
    """

    if metafunc:
        pluginmanager = metafunc.config.pluginmanager
    else:
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
                        content_handlers=content_handlers,
                        prefix=prefix, require_ssl=require_ssl,
                        url=url, use_prior_test=use_prior_test,
                        safe_yaml=safe_yaml, cert_validate=cert_validate)

    test_list = []
    for test in tests:
        if hasattr(test, '_tests'):
            # Establish fixtures as if they were tests. These will
            # be cleaned up by the pytester plugin.
            test_list.append(('start_%s' % test._tests[0].__class__.__name__,
                              test.start, result))
            for subtest in test:
                test_list.append(('%s' % subtest.__class__.__name__,
                                  subtest, result))
            test_list.append(('stop_%s' % test._tests[0].__class__.__name__,
                              test.stop))

    if metafunc:
        if metafunc.function == test_pytest:
            ids = []
            args = []
            for test in test_list:
                if len(test) >= 3:
                    name, method, arg = test
                else:
                    name, method = test
                    arg = None
                ids.append(name)
                args.append((method, arg))

            metafunc.parametrize("test, result", argvalues=args, ids=ids)
    else:
        # preserve backwards compatibility with old calling style
        return test_list


def test_pytest(test, result):
    if result:
        test(result)
    else:
        test()


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
