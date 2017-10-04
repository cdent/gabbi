from collections import OrderedDict
import copy
import unittest
from six.moves import mock

from gabbi import case


class UsePriorTest(unittest.TestCase):

    @staticmethod
    def make_test_case(use_prior_test=None):
        http_case = case.HTTPTestCase('test_request')
        http_case.test_data = copy.copy(case.BASE_TEST)
        if use_prior_test is not None:
            http_case.test_data['use_prior_test'] = use_prior_test
        return http_case

    @mock.patch('gabbi.case.HTTPTestCase._run_test')
    def test_use_prior_set(self, m_run_test):
        http_case = self.make_test_case(True)
        http_case.has_run = False
        http_case.prior = self.make_test_case(True)
        http_case.prior.run = mock.MagicMock(unsafe=True)
        http_case.prior.has_run = False

        http_case.test_request()
        http_case.prior.run.assert_called_once()

    @mock.patch('gabbi.case.HTTPTestCase._run_test')
    def test_use_prior_not_set(self, m_run_test):
        http_case = self.make_test_case(False)
        http_case.has_run = False
        http_case.prior = self.make_test_case(True)
        http_case.prior.run = mock.MagicMock(unsafe=True)
        http_case.prior.has_run = False

        http_case.test_request()
        http_case.prior.run.assert_not_called()