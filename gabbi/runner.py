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

import sys
import yaml
import unittest

from gabbi import driver
from gabbi import case


def run():
    """Run simple tests from STDIN.

    This command provides a way to run a set of tests encoded in YAML that
    is provided on STDIN. No fixtures are supported, so this is primarily
    designed for use with real running services.

    Host and port information may be provided in two different ways:

    * In the URL value of the tests.
    * In a `host` or `host:port` argument on the command line.

    An example run might looks like this::

        gabbi-run example.com:9999 < mytest.yaml

    Output is formatted as unittest summary information.
    """
    try:
        hostport = sys.argv[1]
        if ':' in hostport:
            host, port = hostport.split(':')
        else:
            host = hostport
            port = None
    except IndexError:
        host, port = 'stub', None
    loader = unittest.defaultTestLoader

    # Initialize the extensions for response handling.
    for handler in driver.RESPONSE_HANDLERS:
        handler(case.HTTPTestCase)

    data = yaml.safe_load(sys.stdin.read())
    suite = driver.test_suite_from_yaml(loader, 'input', data, '.',
                                        host, port, None, None)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())


if __name__ == '__main__':
    run()
