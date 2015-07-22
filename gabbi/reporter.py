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

from unittest import TextTestResult
from unittest import TextTestRunner


class ConciseTestResult(TextTestResult):

    def __init__(self, stream, descriptions, verbosity):
        super(ConciseTestResult, self).__init__(
            stream, descriptions, verbosity)

    def startTest(self, test):
        super(TextTestResult, self).startTest(test)
        if self.showAll:
            self.stream.write('... ')
            self.stream.flush()

    def addSuccess(self, test):
        super(TextTestResult, self).addSuccess(test)
        if self.showAll:
            self.stream.write('✓ ')
            self.stream.writeln(self.getDescription(test))

    def addFailure(self, test, err):
        super(TextTestResult, self).addFailure(test, err)
        if self.showAll:
            self.stream.write('✗ ')
            self.stream.writeln(self.getDescription(test))

    def addError(self, test, err):
        super(TextTestResult, self).addError(test, err)
        if self.showAll:
            self.stream.write('E ')
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
            self.stream.writeln('%s: %s' % (flavor, self.getDescription(test)))
            self.stream.writeln('%s:%s:%s' % (err[0], err[1][0][:70], err[2]))
# The rest is left as an exercise for FND
#             details = err.strip().splitlines()[-1]  # traceback's last line
#             if ':' in details:
#                 details = details.split(':', 1)[1]  # discard exception name
#             if True:  # some kind of flag here?
#                 self.stream.writeln('\t%s' % details[:70].strip())
#             else:
#                 self.stream.writeln('%s' % err)


class ConciseTestRunner(TextTestRunner):
    resultclass = ConciseTestResult
