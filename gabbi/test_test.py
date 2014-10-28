#
# Copyright 2014 Red Hat. All Rights Reserved.
#
# Author: Chris Dent <chdent@redhat.com>
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

import unittest


def build_test_method(request, response):
    def test(self):
        self.http_test(request, response)
    return test

class Builder(type):

    def __new__(cls, name, bases, d):

        data_file = d['data_file']
        for p1, p2 in [(1, 2), (2, 2)]:
            d['test_%s_%s' % (data_file, p1)] = build_test_method(p1, p2)

        return type.__new__(cls, name, bases, d)


class HTTPTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print 'setup called', cls.data_file

    def http_test(self, request, response):
        self.assertEqual(request, response)


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()

    for name in ['CowTest', 'PigTest']:
        klass = Builder(name, (HTTPTestCase,), {'data_file': name.lower()})
        tests = loader.loadTestsFromTestCase(klass)
        suite.addTests(tests)

    return suite
