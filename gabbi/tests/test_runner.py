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

import mock
import sys
import unittest
from uuid import uuid4

from six import StringIO
from wsgi_intercept.interceptor import Urllib3Interceptor

from gabbi import driver
from gabbi import handlers
from gabbi import runner
from gabbi.tests.simple_wsgi import SimpleWsgi


class RunnerTest(unittest.TestCase):

    def setUp(self):
        super(RunnerTest, self).setUp()

        # NB: random host ensures that we're not accidentally connecting to an
        #     actual server
        host, port = (str(uuid4()), 8000)
        self.host = host
        self.port = port
        self.server = lambda: Urllib3Interceptor(SimpleWsgi, host, port, '')

        self._stdin = sys.stdin

        self._stdout = sys.stdout
        sys.stdout = StringIO()  # swallow output to avoid confusion

        self._stderr = sys.stderr
        sys.stderr = StringIO()  # swallow output to avoid confusion

        self._argv = sys.argv
        sys.argv = ['gabbi-run', '%s:%s' % (host, port)]

    def tearDown(self):
        sys.stdin = self._stdin
        sys.stdout = self._stdout
        sys.stderr = self._stderr
        sys.argv = self._argv

    def test_target_url_parsing(self):
        sys.argv = ['gabbi-run', 'http://%s:%s/foo' % (self.host, self.port)]

        sys.stdin = StringIO("""
        tests:
        - name: expected success
          GET: /baz
          status: 200
          response_headers:
            x-gabbi-url: http://%s:%s/foo/baz
        """ % (self.host, self.port))
        with self.server():
            try:
                runner.run()
            except SystemExit as err:
                self.assertSuccess(err)

    def test_target_url_parsing_standard_port(self):
        self.server = lambda: Urllib3Interceptor(
            SimpleWsgi, self.host, 80, '')
        sys.argv = ['gabbi-run', 'http://%s/foo' % self.host]

        sys.stdin = StringIO("""
        tests:
        - name: expected success
          GET: /baz
          status: 200
          response_headers:
            x-gabbi-url: http://%s/foo/baz
        """ % self.host)
        with self.server():
            try:
                runner.run()
            except SystemExit as err:
                self.assertSuccess(err)

    def test_custom_response_handler(self):
        sys.stdin = StringIO("""
        tests:
        - name: unknown response handler
          GET: /
          response_html: ...
        """)
        with self.assertRaises(driver.GabbiFormatError):
            runner.run()

        sys.argv.insert(1, "--response-handler")
        sys.argv.insert(2, "gabbi.tests.test_runner:HTMLResponseHandler")

        sys.stdin = StringIO("""
        tests:
        - name: custom response handler
          GET: /presenter
          response_html:
              h1: Hello World
              p: lorem ipsum dolor sit amet
        """)
        with self.server():
            try:
                runner.run()
            except SystemExit as err:
                self.assertSuccess(err)

        sys.stdin = StringIO("""
        tests:
        - name: custom response handler failure
          GET: /presenter
          response_html:
              h1: lipsum
        """)
        with self.server():
            try:
                runner.run()
            except SystemExit as err:
                self.assertFailure(err)

        sys.argv.insert(3, "-r")
        sys.argv.insert(4, "gabbi.tests.test_intercept:TestResponseHandler")

        sys.stdin = StringIO("""
        tests:
        - name: additional custom response handler
          GET: /presenter
          response_html:
              h1: Hello World
          response_test:
          - COWAnother line
        """)
        with self.server():
            try:
                runner.run()
            except SystemExit as err:
                self.assertSuccess(err)

        sys.argv.insert(5, "-r")
        sys.argv.insert(6, "gabbi.tests.custom_response_handler")

        sys.stdin = StringIO("""
        tests:
        - name: custom response handler shorthand
          GET: /presenter
          response_custom:
          - Hello World
          - lorem ipsum dolor sit amet
        """)
        with self.server():
            try:
                runner.run()
            except SystemExit as err:
                self.assertSuccess(err)

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
            self.assertFailure(err)

        sys.stdin = StringIO("""
        tests:
        - name: expected success
          GET: /
          status: 200
        """)
        with self.server():
            try:
                runner.run()
            except SystemExit as err:
                self.assertSuccess(err)

    def assertSuccess(self, exitError):
        errors = exitError.args[0]
        if errors:
            self._dump_captured()
        self.assertEqual(errors, False)

    def assertFailure(self, exitError):
        errors = exitError.args[0]
        if not errors:
            self._dump_captured()
        self.assertEqual(errors, True)

    def _dump_captured(self):
        self._stderr.write('\n==> captured STDOUT <==\n')
        sys.stdout.flush()
        sys.stdout.seek(0)
        self._stderr.write(sys.stdout.read())

        self._stderr.write('\n==> captured STDERR <==\n')
        sys.stderr.flush()
        sys.stderr.seek(0)
        self._stderr.write(sys.stderr.read())


class RunnerHostArgParse(unittest.TestCase):

    @mock.patch('sys.exit')
    @mock.patch('sys.stdin')
    @mock.patch('gabbi.driver.test_suite_from_dict')
    @mock.patch('yaml.safe_load', return_value={})
    def _test_hostport(self, url_or_host, expected_host,
                       portmock_yaml, mock_test_suite, mock_read, mock_exit,
                       provided_prefix=None, expected_port=None,
                       expected_prefix=None, expected_data=None):
        sys.argv = ['gabbi-run', url_or_host]
        if provided_prefix:
            sys.argv.append(provided_prefix)
        runner.run()

        expected_data = expected_data or {}

        mock_test_suite.assert_called_with(
            unittest.defaultTestLoader, 'input', expected_data,
            '.', expected_host, expected_port, None, None,
            prefix=expected_prefix
        )

    def test_plain_url(self):
        self._test_hostport('http://foobar.com:80/news',
                            'foobar.com',
                            expected_port='80',
                            expected_prefix='/news')

    def test_ssl_url(self):
        self._test_hostport('https://foobar.com/news',
                            'foobar.com',
                            expected_prefix='/news',
                            expected_data={'defaults': {'ssl': True}})

    def test_simple_hostport(self):
        self._test_hostport('foobar.com:999',
                            'foobar.com',
                            expected_port='999')

    def test_simple_hostport_with_prefix(self):
        self._test_hostport('foobar.com:999',
                            'foobar.com',
                            provided_prefix='/news',
                            expected_port='999',
                            expected_prefix='/news')

    def test_ipv6_url_long(self):
        self._test_hostport(
            'http://[FEDC:BA98:7654:3210:FEDC:BA98:7654:3210]:999/news',
            'FEDC:BA98:7654:3210:FEDC:BA98:7654:3210',
            expected_port='999',
            expected_prefix='/news')

    def test_ipv6_url_localhost(self):
        self._test_hostport(
            'http://[::1]:999/news',
            '::1',
            expected_port='999',
            expected_prefix='/news')

    def test_ipv6_host_localhost(self):
        # If a user wants to use the hostport form, then they need
        # to hack it with the brackets.
        self._test_hostport(
            '[::1]',
            '::1')

    def test_ipv6_hostport_localhost(self):
        self._test_hostport(
            '[::1]:999',
            '::1',
            expected_port='999')


class HTMLResponseHandler(handlers.ResponseHandler):

    test_key_suffix = 'html'
    test_key_value = {}

    def action(self, test, item, value):
        doc = test.output
        html = '<{tag}>{content}</{tag}>'.format(tag=item, content=value)
        test.assertTrue(html in doc, "no elements matching '%s'" % html)
