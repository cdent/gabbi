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

import copy
import glob
import inspect
import io
import os
import unittest
from unittest import suite
import uuid

import six
import yaml

from gabbi import case
from gabbi import handlers
from gabbi import httpclient
from gabbi import reporter
from gabbi import suite as gabbi_suite


RESPONSE_HANDLERS = [
    handlers.ForbiddenHeadersResponseHandler,
    handlers.HeadersResponseHandler,
    handlers.StringResponseHandler,
    handlers.JSONResponseHandler,
]


class GabbiFormatError(ValueError):
    """An exception to encapsulate poorly formed test data."""
    pass


class TestMaker(object):
    """A class for encapsulating test invariants.

    All of the tests in a single gabbi file have invariants which are
    provided when creating each HTTPTestCase. It is not useful
    to pass these around when making each test case. So they are
    wrapped in this class which then has make_one_test called multiple
    times to generate all the tests in the suite.
    """

    def __init__(self, test_base_name, test_defaults, test_directory,
                 fixture_classes, loader, host, port, intercept, prefix):
        self.test_base_name = test_base_name
        self.test_defaults = test_defaults
        self.default_keys = set(test_defaults.keys())
        self.test_directory = test_directory
        self.fixture_classes = fixture_classes
        self.host = host
        self.port = port
        self.loader = loader
        self.intercept = intercept
        self.prefix = prefix

    def make_one_test(self, test_dict, prior_test):
        """Create one single HTTPTestCase.

        The returned HTTPTestCase is added to the TestSuite currently
        being built (one per YAML file).
        """
        test = copy.deepcopy(self.test_defaults)
        try:
            test_update(test, test_dict)
        except KeyError as exc:
            raise GabbiFormatError('invalid key in test: %s' % exc)
        except AttributeError as exc:
            if not isinstance(test_dict, dict):
                raise GabbiFormatError(
                    'test chunk is not a dict at "%s"' % test_dict)
            else:
                # NOTE(cdent): Not clear this can happen but just in case.
                raise GabbiFormatError(
                    'malformed test chunk "%s": %s' % (test_dict, exc))

        test_name = self._set_test_name(test)
        self._set_test_method_and_url(test, test_name)
        self._validate_keys(test, test_name)

        http_class = httpclient.get_http(verbose=test['verbose'],
                                         caption=test['name'])

        # Use metaclasses to build a class of the necessary type
        # and name with relevant arguments.
        klass = TestBuilder(test_name, (case.HTTPTestCase,),
                            {'test_data': test,
                             'test_directory': self.test_directory,
                             'fixtures': self.fixture_classes,
                             'http': http_class,
                             'host': self.host,
                             'intercept': self.intercept,
                             'port': self.port,
                             'prefix': self.prefix,
                             'prior': prior_test})

        tests = self.loader.loadTestsFromTestCase(klass)
        # Return the first (and only) test in the klass.
        return tests._tests[0]

    def _set_test_name(self, test):
        """Set the name of the test

        The original name is lowercased and spaces are replaces with '_'.
        The result is appended to the test_base_name, which is based on the
        name of the input data file.
        """
        if not test['name']:
            raise GabbiFormatError('Test name missing in a test in %s.'
                                   % self.test_base_name)
        return '%s_%s' % (self.test_base_name,
                          test['name'].lower().replace(' ', '_'))

    @staticmethod
    def _set_test_method_and_url(test, test_name):
        """Extract the base URL and method for this test.

        If there is an upper case key in the test, that is used as the
        method and the value is used as the URL. If there is more than
        one uppercase that is a GabbiFormatError.

        If there is no upper case key then 'url' must be present.
        """
        method_key = None
        for key, val in six.iteritems(test):
            if _is_method_shortcut(key):
                if method_key:
                    raise GabbiFormatError(
                        'duplicate method/URL directive in "%s"' %
                        test_name)

                test['method'] = key
                test['url'] = val
                method_key = key
        if method_key:
            del test[method_key]

        if not test['url']:
            raise GabbiFormatError('Test url missing in test %s.'
                                   % test_name)

    def _validate_keys(self, test, test_name):
        """Check for invalid keys.

        If there are any, raise a GabbiFormatError.
        """
        test_keys = set(test.keys())
        if test_keys != self.default_keys:
            raise GabbiFormatError(
                'Invalid test keys used in test %s: %s'
                % (test_name,
                   ', '.join(list(test_keys - self.default_keys))))


class TestBuilder(type):
    """Metaclass to munge a dynamically created test."""

    required_attributes = {'has_run': False}

    def __new__(mcs, name, bases, attributes):
        attributes.update(mcs.required_attributes)
        return type.__new__(mcs, name, bases, attributes)


def build_tests(path, loader, host=None, port=8001, intercept=None,
                test_loader_name=None, fixture_module=None,
                response_handlers=None, prefix=''):
    """Read YAML files from a directory to create tests.

    Each YAML file represents an ordered sequence of HTTP requests.

    :param path: The directory where yaml files are located.
    :param loader: The TestLoader.
    :param host: The host to test against. Do not use with ``intercept``.
    :param port: The port to test against. Used with ``host``.
    :param intercept: WSGI app factory for wsgi-intercept.
    :param test_loader_name: Base name for test classes. Rarely used.
    :param fixture_module: Python module containing fixture classes.
    :param response_handers: ResponseHandler classes.
    :type response_handlers: List of ResponseHandler classes.
    :param prefix: A URL prefix for all URLs that are not fully qualified.
    :rtype: TestSuite containing multiple TestSuites (one for each YAML file).
    """

    # Exit immediately if we have no host to access, either via a real host
    # or an intercept.
    if not (bool(host) ^ bool(intercept)):
        raise AssertionError('must specify exactly one of host or intercept')

    if test_loader_name is None:
        test_loader_name = inspect.stack()[1]
        test_loader_name = os.path.splitext(os.path.basename(
            test_loader_name[1]))[0]

    # Initialize response handlers.
    response_handlers = response_handlers or []
    for handler in RESPONSE_HANDLERS + response_handlers:
        handler(case.HTTPTestCase)

    top_suite = suite.TestSuite()
    for test_file in glob.iglob('%s/*.yaml' % path):
        if intercept:
            host = str(uuid.uuid4())
        suite_dict = load_yaml(test_file)
        test_base_name = '%s_%s' % (
            test_loader_name, os.path.splitext(os.path.basename(test_file))[0])
        file_suite = test_suite_from_dict(loader, test_base_name, suite_dict,
                                          path, host, port, fixture_module,
                                          intercept, prefix)
        top_suite.addTest(file_suite)
    return top_suite


def py_test_generator(test_dir, host=None, port=8001, intercept=None,
                      prefix=None, test_loader_name=None,
                      fixture_module=None, response_handlers=None):
    """Generate tests cases for py.test

    This uses build_tests to create TestCases and then yields them in
    a way that pytest can handle.
    """
    loader = unittest.TestLoader()
    result = reporter.PyTestResult()
    tests = build_tests(test_dir, loader, host=host, port=port,
                        intercept=intercept,
                        test_loader_name=test_loader_name,
                        fixture_module=fixture_module,
                        response_handlers=response_handlers,
                        prefix=prefix)

    for test in tests:
        if hasattr(test, '_tests'):
            # Establish fixtures as if they were tests.
            yield 'start_%s' % test._tests[0].__class__.__name__, \
                test.start, result
            for subtest in test:
                yield '%s' % subtest.__class__.__name__, subtest, result
            yield 'stop_%s' % test._tests[0].__class__.__name__, test.stop


def load_yaml(yaml_file):
    """Read and parse any YAML file. Let exceptions flow where they may."""
    with io.open(yaml_file, encoding='utf-8') as source:
        return yaml.safe_load(source.read())


def test_update(orig_dict, new_dict):
    """Modify test in place to update with new data."""
    for key, val in six.iteritems(new_dict):
        if key == 'data':
            orig_dict[key] = val
        elif isinstance(val, dict):
            orig_dict[key].update(val)
        elif isinstance(val, list):
            orig_dict[key] = orig_dict.get(key, []) + val
        else:
            orig_dict[key] = val


def test_suite_from_dict(loader, test_base_name, suite_dict, test_directory,
                         host, port, fixture_module, intercept, prefix=''):
    """Generate a TestSuite from YAML-sourced data."""
    try:
        test_data = suite_dict['tests']
    except KeyError:
        raise GabbiFormatError('malformed test file, "tests" key required')
    except TypeError:
        # `suite_dict` appears not to be a dictionary; we cannot infer
        # any details or suggestions on how to fix it, thus discarding
        # the original exception in favor of a generic error
        raise GabbiFormatError('malformed test file, invalid format')

    # Merge global with per-suite defaults
    default_test_dict = copy.deepcopy(case.HTTPTestCase.base_test)
    local_defaults = _validate_defaults(suite_dict.get('defaults', {}))
    test_update(default_test_dict, local_defaults)

    # Establish any fixture classes used in this file.
    fixtures = suite_dict.get('fixtures', None)
    fixture_classes = []
    if fixtures and fixture_module:
        for fixture_class in fixtures:
            fixture_classes.append(getattr(fixture_module, fixture_class))

    test_maker = TestMaker(test_base_name, default_test_dict, test_directory,
                           fixture_classes, loader, host, port, intercept,
                           prefix)
    file_suite = gabbi_suite.GabbiSuite()
    prior_test = None
    for test_dict in test_data:
        this_test = test_maker.make_one_test(test_dict, prior_test)
        file_suite.addTest(this_test)
        prior_test = this_test

    return file_suite


def test_suite_from_yaml(loader, test_base_name, test_yaml, test_directory,
                         host, port, fixture_module, intercept, prefix=''):
    """Legacy wrapper retained for backwards compatibility."""
    import warnings

    with warnings.catch_warnings():  # ensures warnings filter is restored
        warnings.simplefilter('default', DeprecationWarning)
        warnings.warn('test_suite_from_yaml has been renamed to '
                      'test_suite_from_dict', DeprecationWarning, stacklevel=2)
    return test_suite_from_dict(loader, test_base_name, test_yaml,
                                test_directory, host, port, fixture_module,
                                intercept, prefix)


def _validate_defaults(defaults):
    """Ensure default test settings are acceptable.

    Raises GabbiFormatError for invalid settings.
    """
    if any(_is_method_shortcut(key) for key in defaults):
        raise GabbiFormatError('"METHOD: url" pairs not allowed in defaults')
    return defaults


def _is_method_shortcut(key):
    """Is this test key indicating a request method.

    It is a request method if it is all upper case.
    """
    return key.isupper()
