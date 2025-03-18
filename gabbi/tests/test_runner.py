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

from io import StringIO
import os
import subprocess
import socket
import sys
import time
import unittest

from gabbi import exception
from gabbi.handlers import base
from gabbi.handlers.jsonhandler import JSONHandler
from gabbi import runner


def get_free_port():
    sock = socket.socket()
    sock.bind(('', 0))
    return sock.getsockname()[1]

class ForkedWSGIServer:

    def __init__(self, port):
        self.port = port

    def start(self):
        self.process = subprocess.Popen([
            "python", "gabbi/tests/external_server.py", str(self.port)],
            env=os.environ.update({"PYTHONPATH": "."}),
            close_fds=True)
        # We need to sleep a bit to let the wsgi server start.
        time.sleep(.2)

    def stop(self):
        self.process.terminate()


class RunnerTest(unittest.TestCase):

    port = get_free_port()

    def setUp(self):
        super(RunnerTest, self).setUp()

        self.host = "localhost"
        self.resolved_host = "1.0.0.127.in-addr.arpa"
        self.server = ForkedWSGIServer(self.port)
        self.server.start()

        self._stdin = sys.stdin

        self._stdout = sys.stdout
        sys.stdout = StringIO()  # swallow output to avoid confusion

        self._stderr = sys.stderr
        sys.stderr = StringIO()  # swallow output to avoid confusion

        self._argv = sys.argv
        sys.argv = ['gabbi-run', '%s:%s' % (self.host, self.port)]

    def tearDown(self):
        sys.stdin = self._stdin
        sys.stdout = self._stdout
        sys.stderr = self._stderr
        sys.argv = self._argv
        self.server.stop()

    def test_input_files(self):
        sys.argv = ['gabbi-run', 'http://%s:%s/foo' % (self.host, self.port)]

        sys.argv.append('--')
        sys.argv.append('gabbi/tests/gabbits_runner/success.yaml')

        try:
            runner.run()
        except SystemExit as err:
            self.assertSuccess(err)

        sys.argv.append('gabbi/tests/gabbits_runner/failure.yaml')

        try:
            runner.run()
        except SystemExit as err:
            self.assertFailure(err)

        sys.argv.append('gabbi/tests/gabbits_runner/success_alt.yaml')

        try:
            runner.run()
        except SystemExit as err:
            self.assertFailure(err)

    def test_unsafe_yaml(self):
        sys.argv = ['gabbi-run', 'http://%s:%s/nan' % (self.host, self.port)]

        sys.argv.append('--unsafe-yaml')
        sys.argv.append('--')
        sys.argv.append('gabbi/tests/gabbits_runner/nan.yaml')

        try:
            runner.run()
        except SystemExit as err:
            self.assertSuccess(err)

    def test_target_url_parsing(self):
        sys.argv = ['gabbi-run', 'http://%s:%s/foo' % (self.host, self.port)]

        sys.stdin = StringIO("""
        tests:
        - name: expected success
          GET: /baz
          status: 200
          response_headers:
            x-gabbi-url: http://%s:%s/foo/baz
        """ % (self.resolved_host, self.port))
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
        with self.assertRaises(exception.GabbiFormatError):
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

        try:
            runner.run()
        except SystemExit as err:
            self.assertFailure(err)

        sys.argv.insert(3, "-r")
        sys.argv.insert(4, "gabbi.tests.test_intercept:StubResponseHandler")

        sys.stdin = StringIO("""
        tests:
        - name: additional custom response handler
          GET: /presenter
          response_html:
              h1: Hello World
          response_test:
          - COWAnother line
        """)

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

        try:
            runner.run()
        except SystemExit as err:
            self.assertSuccess(err)

    def test_exit_code(self):
        sys.stdin = StringIO()
        with self.assertRaises(exception.GabbiFormatError):
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

        try:
            runner.run()
        except SystemExit as err:
            self.assertSuccess(err)

    def test_verbose_output_formatting(self):
        """Confirm that a verbose test handles output properly."""
        sys.argv = ['gabbi-run', 'http://%s:%s/foo' % (self.host, self.port)]

        sys.argv.append('--')
        sys.argv.append('gabbi/tests/gabbits_runner/test_verbose.yaml')

        try:
            runner.run()
        except SystemExit as err:
            self.assertSuccess(err)

        sys.stdout.seek(0)
        output = sys.stdout.read()
        self.assertIn('"our text"', output)
        self.assertIn('"cow": "moo"', output)
        self.assertIn('"dog": "bark"', output)
        # confirm pretty printing
        self.assertIn('{\n', output)
        self.assertIn('}\n', output)

    def test_data_dir_good(self):
        """Confirm that data dir is the test file's dir."""
        sys.argv = ['gabbi-run', 'http://%s:%s/foo' % (self.host, self.port)]

        sys.argv.append('--')
        sys.argv.append('gabbi/tests/gabbits_runner/test_data.yaml')

        try:
            runner.run()
        except SystemExit as err:
            self.assertSuccess(err)

        # Compare the verbose output of tests with pretty printed
        # data.
        with open('gabbi/tests/gabbits_runner/subdir/sample.json') as data:
            data = JSONHandler.loads(data.read())
            expected_string = JSONHandler.dumps(data, pretty=True)

        sys.stdout.seek(0)
        output = sys.stdout.read()
        self.assertIn(expected_string, output)

    def test_stdin_data_dir(self):
        """Confirm data dir as '.' when reading from stdin."""
        sys.stdin = StringIO("""
        tests:
        - name: expected success
          POST: /
          request_headers:
            content-type: application/json
          data: <@gabbi/tests/gabbits_runner/subdir/sample.json
          response_json_paths:
            $.items.house: blue
        """)

        try:
            runner.run()
        except SystemExit as err:
            self.assertSuccess(err)

    def _run_verbosity_arg(self):
        sys.argv.append('--')
        sys.argv.append('gabbi/tests/gabbits_runner/verbosity.yaml')

        try:
            runner.run()
        except SystemExit as err:
            self.assertSuccess(err)

        sys.stdout.seek(0)
        output = sys.stdout.read()
        return output

    def test_verbosity_arg_none(self):
        """Confirm --verbose handling."""
        sys.argv = ['gabbi-run', 'http://%s:%s/foo' % (self.host, self.port)]

        output = self._run_verbosity_arg()
        self.assertEqual('', output)

    def test_verbosity_arg_body(self):
        """Confirm --verbose handling."""
        sys.argv = ['gabbi-run', 'http://%s:%s/foo' % (self.host, self.port),
                    '--verbose=body']

        output = self._run_verbosity_arg()
        self.assertIn('{\n  "cat": "poppy"\n}', output)
        self.assertNotIn('application/json', output)

    def test_verbosity_arg_headers(self):
        """Confirm --verbose handling."""
        sys.argv = ['gabbi-run', 'http://%s:%s/foo' % (self.host, self.port),
                    '--verbose=headers']

        output = self._run_verbosity_arg()
        self.assertNotIn('{\n  "cat": "poppy"\n}', output)
        self.assertIn('application/json', output)

    def test_verbosity_arg_all(self):
        """Confirm --verbose handling."""
        sys.argv = ['gabbi-run', 'http://%s:%s/foo' % (self.host, self.port),
                    '--verbose=all']

        output = self._run_verbosity_arg()
        self.assertIn('{\n  "cat": "poppy"\n}', output)
        self.assertIn('application/json', output)

    def test_quiet_is_quiet(self):
        """Confirm -q shuts down output."""
        sys.argv = [
            'gabbi-run', '-q', 'http://%s:%s/foo' % (self.host, self.port)]

        sys.stdin = StringIO("""
        tests:
        - name: expected success
          GET: /baz
          status: 200
          response_headers:
            x-gabbi-url: http://%s:%s/foo/baz
        """ % (self.host, self.port))

        try:
            runner.run()
        except SystemExit as err:
            self.assertSuccess(err)

        sys.stdout.seek(0)
        sys.stderr.seek(0)
        stdoutput = sys.stdout.read()
        stderror = sys.stderr.read()
        self.assertEqual('', stdoutput)
        self.assertEqual('', stderror)

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


class HTMLResponseHandler(base.ResponseHandler):

    test_key_suffix = 'html'
    test_key_value = {}

    def action(self, test, item, value=None):
        doc = test.output
        html = '<{tag}>{content}</{tag}>'.format(tag=item, content=value)
        test.assertIn(html, doc, "no elements matching '%s'" % html)
