
import glob
import os
import unittest


def build_test_method(request, response):
    def test(self):
        self.http_test(request, response)
    return test


class Builder(type):

    def __new__(cls, name, bases, d):

        data_file = d['data_file']
        for p1, p2 in [(1, 2), (2, 2)]:
            d['test_%s_%s' % (name, p1)] = build_test_method(p1, p2)

        return type.__new__(cls, name, bases, d)


class HTTPTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print 'setup called', cls.data_file

    def http_test(self, request, response):
        self.assertEqual(request, response)


def build_tests(path, loader, tests, pattern):
    suite = unittest.TestSuite()

    path = '%s/*.yaml' % path

    for test_file in glob.iglob(path):
        test_name = os.path.splitext(os.path.basename(test_file))[0]
        klass = Builder(test_name, (HTTPTestCase,), {'data_file': test_file})
        tests = loader.loadTestsFromTestCase(klass)
        suite.addTests(tests)

    return suite
