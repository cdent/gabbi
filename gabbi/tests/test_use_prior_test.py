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
"""Test use_prior_test directive.
"""

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
    def test_use_prior_true(self, m_run_test):
        http_case = self.make_test_case(True)
        http_case.has_run = False
        http_case.prior = self.make_test_case(True)
        http_case.prior.run = mock.MagicMock(unsafe=True)
        http_case.prior.has_run = False

        http_case.test_request()
        http_case.prior.run.assert_called_once()

    @mock.patch('gabbi.case.HTTPTestCase._run_test')
    def test_use_prior_false(self, m_run_test):
        http_case = self.make_test_case(False)
        http_case.has_run = False
        http_case.prior = self.make_test_case(True)
        http_case.prior.run = mock.MagicMock(unsafe=True)
        http_case.prior.has_run = False

        http_case.test_request()
        http_case.prior.run.assert_not_called()

    @mock.patch('gabbi.case.HTTPTestCase._run_test')
    def test_use_prior_default_true(self, m_run_test):
        http_case = self.make_test_case()
        http_case.has_run = False
        http_case.prior = self.make_test_case(True)
        http_case.prior.run = mock.MagicMock(unsafe=True)
        http_case.prior.has_run = False

        http_case.test_request()
        http_case.prior.run.assert_called_once()
