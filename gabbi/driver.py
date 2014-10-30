
import glob
import os
import unittest

import yaml


def build_test_method(test):
    def test(self):
        self.http_test(test)
    return test


def load_yaml(yaml_file):
    with open(yaml_file) as source:
        return yaml.safe_load(source.read())



class Builder(type):

    def __new__(cls, name, bases, d):

        test_data = load_yaml(d['data_file'])

        for test in test_data:
            test_name = test['name'].lower().replace(' ', '_')
            d['test_%s' % test_name] = build_test_method(test)

        return type.__new__(cls, name, bases, d)


class HTTPTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print 'setup called', cls.data_file

    def http_test(self, test):
        self.assertTrue(test)


def build_tests(path, loader, tests, pattern):
    suite = unittest.TestSuite()

    path = '%s/*.yaml' % path

    for test_file in glob.iglob(path):
        test_name = os.path.splitext(os.path.basename(test_file))[0]
        klass = Builder(test_name, (HTTPTestCase,), {'data_file': test_file})
        tests = loader.loadTestsFromTestCase(klass)
        suite.addTests(tests)

    return suite
