
import glob
import os

import testtools
import yaml

from unittest import suite


def load_yaml(yaml_file):
    with open(yaml_file) as source:
        return yaml.safe_load(source.read())


class Builder(type):

    def __new__(cls, name, bases, d):
        return type.__new__(cls, name, bases, d)


class HTTPTestCase(testtools.TestCase):

    def setUp(self):
        if not self.has_run:
            super(HTTPTestCase, self).setUp()

    def tearDown(self):
        if not self.has_run:
            super(HTTPTestCase, self).tearDown()
        self.has_run = True

    def runTest(self):
        if self.has_run:
            return
        if self.prior and not self.prior.has_run:
            self.prior.run()
        self.assertTrue(self.test_data['url'])


def build_tests(path, loader, tests, pattern):
    top_suite = suite.TestSuite()

    path = '%s/*.yaml' % path

    for test_file in glob.iglob(path):
        file_suite = suite.TestSuite()
        test_data = load_yaml(test_file)
        test_base_name = os.path.splitext(os.path.basename(test_file))[0]
        prior_test = None
        for test in test_data:
            test_name = '%s_%s' % (test_base_name,
                                   test['name'].lower().replace(' ', '_'))
            klass = Builder(test_name, (HTTPTestCase,),
                            {'test_data': test,
                             'prior': prior_test,
                             'has_run': False})
            tests = loader.loadTestsFromTestCase(klass)
            this_test = tests._tests[0]
            file_suite.addTest(this_test)
            prior_test = this_test
        top_suite.addTest(file_suite)

    return top_suite
