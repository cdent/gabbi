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
"""Implementation of a command-line runner of single gabbi files."""

import argparse
from importlib import import_module
import sys
import unittest

from gabbi import case
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

    Use `-x` or `--failfast` to abort after the first error or failure:

        gabbi-run -x example.com:9999 /mountpoint < mytest.yaml

    Output is formatted as unittest summary information.
    """

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

    args = parser.parse_args()
    host, port, prefix, force_ssl = utils.host_info_from_target(
        args.target, args.prefix)

    # Initialize response handlers.
    initialize_handlers(args.response_handlers)

    data = utils.load_yaml(handle=sys.stdin)
    if force_ssl:
        if 'defaults' in data:
            data['defaults']['ssl'] = True
        else:
            data['defaults'] = {'ssl': True}
    loader = unittest.defaultTestLoader
    test_suite = suitemaker.test_suite_from_dict(
        loader, 'input', data, '.', host, port, None, None, prefix=prefix)
    result = ConciseTestRunner(
        verbosity=2, failfast=args.failfast).run(test_suite)
    sys.exit(not result.wasSuccessful())


def initialize_handlers(response_handlers):
    custom_response_handlers = []
    for import_path in response_handlers or []:
        for handler in load_response_handlers(import_path):
            custom_response_handlers.append(handler)
    for handler in handlers.RESPONSE_HANDLERS + custom_response_handlers:
        handler(case.HTTPTestCase)


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
        handlers = [handler]
    else:  # package.module shorthand, expecting gabbi_response_handlers
        module = import_module(import_path)
        handlers = module.gabbi_response_handlers
        if callable(handlers):
            handlers = handlers()
    return handlers


if __name__ == '__main__':
    run()
