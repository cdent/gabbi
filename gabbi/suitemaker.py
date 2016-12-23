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
"""The code that creates a suite of tests.

The key piece of code is :meth:`test_suite_from_dict`. It produces a
:class:`gabbi.suite.GabbiSuite` containing one or more
:class:`gabbi.case.HTTPTestCase`.
"""

import copy

from gabbi import case
from gabbi.exception import GabbiFormatError
from gabbi import httpclient
from gabbi import suite


class TestMaker(object):
    """A class for encapsulating test invariants.

    All of the tests in a single gabbi file have invariants which are
    provided when creating each HTTPTestCase. It is not useful
    to pass these around when making each test case. So they are
    wrapped in this class which then has make_one_test called multiple
    times to generate all the tests in the suite.
    """

    def __init__(self, test_base_name, test_defaults, test_directory,
                 fixture_classes, loader, host, port, intercept, prefix,
                 response_handlers, content_handlers, test_loader_name=None,
                 inner_fixtures=None):
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
        self.test_loader_name = test_loader_name
        self.inner_fixtures = inner_fixtures or []
        self.content_handlers = content_handlers
        self.response_handlers = response_handlers

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
        if prior_test:
            history = prior_test.history
        else:
            history = {}

        # Use metaclasses to build a class of the necessary type
        # and name with relevant arguments.
        klass = TestBuilder(test_name, (case.HTTPTestCase,),
                            {'test_data': test,
                             'test_directory': self.test_directory,
                             'fixtures': self.fixture_classes,
                             'inner_fixtures': self.inner_fixtures,
                             'http': http_class,
                             'host': self.host,
                             'intercept': self.intercept,
                             'content_handlers': self.content_handlers,
                             'response_handlers': self.response_handlers,
                             'port': self.port,
                             'prefix': self.prefix,
                             'prior': prior_test,
                             'history': history,
                             })
        # We've been asked to, make this test class think it comes
        # from a different module.
        if self.test_loader_name:
            klass.__module__ = self.test_loader_name

        tests = self.loader.loadTestsFromTestCase(klass)
        history[test['name']] = tests._tests[0]
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
        for key, val in test.items():
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


def test_suite_from_dict(loader, test_base_name, suite_dict, test_directory,
                         host, port, fixture_module, intercept, prefix='',
                         handlers=None, test_loader_name=None,
                         inner_fixtures=None):
    """Generate a GabbiSuite from a dict represent a list of tests.

    The dict takes the form:

    :param fixtures: An optional list of fixture classes that this suite
                     can use.
    :param defaults: An optional dictionary of default values to be used
                     in each test.
    :param tests: A list of individual tests, themselves each being a
                  dictionary. See :data:`gabbi.case.BASE_TEST`.
    """
    try:
        test_data = suite_dict['tests']
    except KeyError:
        raise GabbiFormatError('malformed test file, "tests" key required')
    except TypeError:
        # `suite_dict` appears not to be a dictionary; we cannot infer
        # any details or suggestions on how to fix it, thus discarding
        # the original exception in favor of a generic error
        raise GabbiFormatError('malformed test file, invalid format')

    handlers = handlers or []
    response_handlers = []
    content_handlers = []

    # Merge global with per-suite defaults
    default_test_dict = copy.deepcopy(case.HTTPTestCase.base_test)
    for handler in handlers:
        default_test_dict.update(handler.test_base)
        if handler.response_handler:
            response_handlers.append(handler.response_handler)
        if handler.content_handler:
            content_handlers.append(handler.content_handler)

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
                           prefix, response_handlers, content_handlers,
                           test_loader_name=test_loader_name,
                           inner_fixtures=inner_fixtures)
    file_suite = suite.GabbiSuite()
    prior_test = None
    for test_dict in test_data:
        this_test = test_maker.make_one_test(test_dict, prior_test)
        file_suite.addTest(this_test)
        prior_test = this_test

    return file_suite


def test_update(orig_dict, new_dict):
    """Modify test in place to update with new data."""
    for key, val in new_dict.items():
        if key == 'data':
            orig_dict[key] = val
        elif isinstance(val, dict):
            orig_dict[key].update(val)
        elif isinstance(val, list):
            orig_dict[key] = orig_dict.get(key, []) + val
        else:
            orig_dict[key] = val


def _is_method_shortcut(key):
    """Is this test key indicating a request method.

    It is a request method if it is all upper case.
    """
    return key.isupper()


def _validate_defaults(defaults):
    """Ensure default test settings are acceptable.

    Raises GabbiFormatError for invalid settings.
    """
    if any(_is_method_shortcut(key) for key in defaults):
        raise GabbiFormatError('"METHOD: url" pairs not allowed in defaults')
    return defaults
