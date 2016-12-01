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
"""Implementation of a command-line runner for gabbi files (AKA suites)."""

import argparse
from importlib import import_module
import os
import sys
import unittest

from gabbi import handlers
from gabbi.reporter import ConciseTestRunner
from gabbi import suitemaker
from gabbi import utils


def run():
    """Run simple tests from STDIN.

    This command provides a way to run a set of tests encoded in YAML that
    is provided on STDIN. No fixtures are supported, so this is primarily
    designed for use with real running services.

    Host and port information may be provided in three different ways:

    * In the URL value of the tests.
    * In a `host` or `host:port` argument on the command line.
    * In a URL on the command line.

    An example run might looks like this::

        gabbi-run example.com:9999 < mytest.yaml

    or::

        gabbi-run http://example.com:999 < mytest.yaml

    It is also possible to provide a URL prefix which can be useful if the
    target application might be mounted in different locations. An example::

        gabbi-run example.com:9999 /mountpoint < mytest.yaml

    or::

        gabbi-run http://example.com:9999/mountpoint < mytest.yaml

    Use `-x` or `--failfast` to abort after the first error or failure::

        gabbi-run -x example.com:9999 /mountpoint < mytest.yaml

    Use `-v` or `--verbose` with a value of `all`, `headers` or `body` to
    turn on verbosity for all tests being run.

    Multiple files may be named as arguments, separated from other arguments
    by a ``--``. Each file will be run as a separate test suite::

        gabbi-run http://example.com -- /path/to/x.yaml /path/to/y.yaml

    Output is formatted as unittest summary information.
    """
    parser = _make_argparser()

    argv, input_files = extract_file_paths(sys.argv)
    args = parser.parse_args(argv[1:])

    host, port, prefix, force_ssl = utils.host_info_from_target(
        args.target, args.prefix)

    handler_objects = initialize_handlers(args.response_handlers)

    verbosity = args.verbosity
    failfast = args.failfast
    failure = False

    if not input_files:
        success = run_suite(sys.stdin, handler_objects, host, port,
                            prefix, force_ssl, failfast,
                            verbosity=verbosity)
        failure = not success
    else:
        for input_file in input_files:
            with open(input_file, 'r') as fh:
                data_dir = os.path.dirname(input_file)
                success = run_suite(fh, handler_objects, host, port,
                                    prefix, force_ssl, failfast,
                                    data_dir=data_dir,
                                    verbosity=verbosity)
            if not failure:  # once failed, this is considered immutable
                failure = not success
            if failure and failfast:
                break

    sys.exit(failure)


def run_suite(handle, handler_objects, host, port, prefix, force_ssl=False,
              failfast=False, data_dir='.', verbosity=False):
    """Run the tests from the YAML in handle."""
    data = utils.load_yaml(handle)
    if force_ssl:
        if 'defaults' in data:
            data['defaults']['ssl'] = True
        else:
            data['defaults'] = {'ssl': True}
    if verbosity:
        if 'defaults' in data:
            data['defaults']['verbose'] = verbosity
        else:
            data['defaults'] = {'verbose': verbosity}

    loader = unittest.defaultTestLoader
    test_suite = suitemaker.test_suite_from_dict(
        loader, 'input', data, data_dir, host, port, None, None, prefix=prefix,
        handlers=handler_objects)

    result = ConciseTestRunner(
        verbosity=2, failfast=failfast).run(test_suite)
    return result.wasSuccessful()


def initialize_handlers(response_handlers):
    custom_response_handlers = []
    handler_objects = []
    for import_path in response_handlers or []:
        for handler in load_response_handlers(import_path):
            custom_response_handlers.append(handler)
    for handler in handlers.RESPONSE_HANDLERS + custom_response_handlers:
        handler_objects.append(handler())
    return handler_objects


def load_response_handlers(import_path):
    """Load and return custom response handlers from the given Python package
    or module.

    The import path references either a specific response handler class
    ("package.module:class") or a module that contains one or more response
    handler classes ("package.module").

    For the latter, the module is expected to contain a
    ``gabbi_response_handlers`` object, which is either a list of response
    handler classes or a function returning such a list.
    """
    if ":" in import_path:  # package.module:class
        module_name, handler_name = import_path.rsplit(":", 1)
        module = import_module(module_name)
        handler = getattr(module, handler_name)
        custom_handlers = [handler]
    else:  # package.module shorthand, expecting gabbi_response_handlers
        module = import_module(import_path)
        custom_handlers = module.gabbi_response_handlers
        if callable(custom_handlers):
            custom_handlers = custom_handlers()
    return custom_handlers


def extract_file_paths(argv):
    """Extract command-line arguments following the `--` end-of-options
    delimiter, if any.
    """
    try:  # extract file paths, separated by `--`
        i = argv.index("--")
        input_files = argv[i + 1:]
        argv = argv[:i]
    except ValueError:
        input_files = None

    return argv, input_files


def _make_argparser():
    """Set up the argparse.ArgumentParser."""
    parser = argparse.ArgumentParser(description='Run gabbi tests from STDIN')
    parser.add_argument(
        'target',
        nargs='?', default='stub',
        help='A fully qualified URL (with optional path as prefix) '
             'to the primary target or a host and port, : separated. '
             'If using an IPV6 address for the host in either form, '
             'wrap it in \'[\' and \']\'.'
    )
    parser.add_argument(
        'prefix',
        nargs='?', default=None,
        help='Path prefix where target app is mounted. Only used when '
             'target is of the form host[:port]'
    )
    parser.add_argument(
        '-x', '--failfast',
        action='store_true',
        help='Exit on first failure'
    )
    parser.add_argument(
        '-r', '--response-handler',
        nargs='?', default=None,
        dest='response_handlers',
        action='append',
        help='Custom response handler. Should be an import path of the '
             'form package.module or package.module:class.'
    )
    parser.add_argument(
        '-v', '--verbose',
        dest='verbosity',
        choices=['all', 'body', 'headers'],
        help='Turn on test verbosity for all tests run in this session.'
    )
    return parser


if __name__ == '__main__':
    run()
