# coding: utf-8

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
"""TestRunner and TestResult for gabbi-run."""

from unittest import TestResult
from unittest import TextTestResult
from unittest import TextTestRunner

import pytest

from gabbi import utils


class ConciseTestResult(TextTestResult):
    """A TextTestResult with simple but useful output.

    If the output is a tty or GABBI_FORCE_COLOR is set in the
    environment, output will be colorized.
    """

    def __init__(self, stream, descriptions, verbosity):
        super(ConciseTestResult, self).__init__(
            stream, descriptions, verbosity)
        self.colorize = utils.get_colorizer(stream)

    def startTest(self, test):
        super(TextTestResult, self).startTest(test)
        if self.showAll:
            self.stream.write('... ')
            self.stream.flush()

    def addSuccess(self, test):
        super(TextTestResult, self).addSuccess(test)
        if self.showAll:
            self.stream.write(self.colorize('GREEN', '✓ '))
            self.stream.writeln(self.getDescription(test))

    def addFailure(self, test, err):
        super(TextTestResult, self).addFailure(test, err)
        if self.showAll:
            self.stream.write(self.colorize('RED', '✗ '))
            self.stream.writeln(self.getDescription(test))

    def addError(self, test, err):
        super(TextTestResult, self).addError(test, err)
        if self.showAll:
            self.stream.write(self.colorize('RED', 'E '))
            self.stream.writeln(self.getDescription(test))

    def addSkip(self, test, reason):
        super(TextTestResult, self).addSkip(test, reason)
        if self.showAll:
            self.stream.write('- ')
            self.stream.writeln(self.getDescription(test))
            self.stream.writeln('\t[skipped] {0!r}'.format(reason))

    def addExpectedFailure(self, test, err):
        super(TextTestResult, self).addExpectedFailure(test, err)
        if self.showAll:
            self.stream.write('o ')
            self.stream.writeln(self.getDescription(test))
            self.stream.writeln('\t[expected failure]')

    def addUnexpectedSuccess(self, test):
        super(TextTestResult, self).addUnexpectedSuccess(test)
        if self.showAll:
            self.stream.write('! ')
            self.stream.writeln(self.getDescription(test))
            self.stream.writeln('\t[unexpected success]')

    def getDescription(self, test):
        name = test.test_data['name']
        desc = test.test_data.get('desc', None)
        return ': '.join((name, desc)) if desc else name

    def _exc_info_to_string(self, err, test):
        """Override exception to string handling

        The default does too much. We don't want doctoring. We want
        information!
        """
        return err

    def printErrorList(self, flavor, errors):
        for test, err in errors:
            # err[0] is the type of exception
            # err[1] is the args of the exception
            # err[3] is the traceback, not currently used
            self.stream.writeln('%s: %s' % (flavor, self.getDescription(test)))
            message = str(err[1])
            for line in message.splitlines():
                self.stream.writeln('\t%s' % line)


class PyTestResult(TestResult):
    """Wrap a test result to allow it to work with pytest.

    The main behaviors here are:

    * to turn what had been exceptions back into exceptions
    * use pytest's skip and xfail methods
    """

    def addFailure(self, test, err):
        raise err[1]

    def addError(self, test, err):
        raise err[1]

    def addSkip(self, test, reason):
        pytest.skip(reason)

    def addExpectedFailure(self, test, err):
        pytest.xfail('%s' % err[1])


class ConciseTestRunner(TextTestRunner):
    """A TextTestRunner that uses ConciseTestResult for reporting results."""
    resultclass = ConciseTestResult
