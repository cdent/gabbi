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
"""Test that the CLI works as expected
"""

import sys
import unittest

from six import StringIO

from gabbi import runner
from gabbi import driver
from gabbi.fixture import InterceptFixture
from gabbi.simple_wsgi import SimpleWsgi


class RunnerTest(unittest.TestCase):

    def setUp(self):
        super(RunnerTest, self).setUp()

        self._stdin = sys.stdin

        self._stdout = sys.stdout
        sys.stdout = StringIO()  # swallow output to avoid confusion

        self._stderr = sys.stderr
        sys.stderr = StringIO()  # swallow output to avoid confusion

        self._argv = sys.argv
        sys.argv = ['gabbi-run']

    def tearDown(self):
        sys.stdin = self._stdin
        sys.stdout = self._stdout
        sys.stderr = self._stderr
        sys.argv = self._argv

    def test_exit_code(self):
        sys.stdin = StringIO()
        with self.assertRaises(driver.GabbiFormatError):
            runner.run()

        sys.stdin = StringIO("""
        tests:
        - name: expected failure
          GET: /
          status: 666
        """)
        try:
            runner.run()
        except SystemExit as err:
            self.assertEqual(err.args[0], True)

        sys.stdin = StringIO("""
        tests:
        - name: expected success
          GET: /
          status: 200
        """)
        host, port = ('example.com', '80')
        sys.argv.append('%s:%s' % (host, port))
        with InterceptFixture(host, port, SimpleWsgi, ''):
            try:
                runner.run()
            except SystemExit as err:
                self.assertEqual(err.args[0], False)
