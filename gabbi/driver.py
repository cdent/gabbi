
import glob
import os

import testresources
import yaml


def load_yaml(yaml_file):
    with open(yaml_file) as source:
        return yaml.safe_load(source.read())


class Builder(type):

    def __new__(cls, name, bases, d):
        return type.__new__(cls, name, bases, d)


class HTTPTestCase(testresources.ResourcedTestCase):

    def runTest(self):
        self.assertTrue(self.test_data['url'])


class PriorTest(testresources.TestResourceManager):

    def __init__(self, suite, prior):
        self.suite = suite
        self.prior = prior
        super(PriorTest, self).__init__()

    def make(self, dependency):
        self.prior.run(testresources._get_result())

    def isDirty(self):
        return False


def build_tests(path, loader, tests, pattern):
    top_suite = testresources.OptimisingTestSuite()

    path = '%s/*.yaml' % path

    for test_file in glob.iglob(path):
        file_suite = testresources.OptimisingTestSuite()
        test_data = load_yaml(test_file)
        test_base_name = os.path.splitext(os.path.basename(test_file))[0]
        prior_test = None
        for test in test_data:
            test_name = '%s_%s' % (test_base_name,
                                   test['name'].lower().replace(' ', '_'))
            klass = Builder(test_name, (HTTPTestCase,),
                            {'test_data': test})
            if prior_test:
                klass.resources = [('prior',
                                    PriorTest(file_suite, prior_test))]
            tests = loader.loadTestsFromTestCase(klass)
            this_test = tests._tests[0]
            file_suite.addTest(this_test)
            prior_test = this_test
        top_suite.addTest(file_suite)

    return top_suite
