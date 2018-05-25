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
"""Test loading data from files with <@.
"""

import unittest

from six.moves import mock

from gabbi import case


@mock.patch(
    'gabbi.case.open',
    new_callable=mock.mock_open,
    read_data='dummy content',
    create=True,
)
class DataFileTest(unittest.TestCase):
    """Test reading files in tests.

    Reading from local files is only allowed at or below the
    test_directory level.
    """

    def setUp(self):
        self.http_case = case.HTTPTestCase('test_request')

    def _assert_content_read(self, filepath):
        self.assertEqual(
            'dummy content', self.http_case.load_data_file(filepath))

    def test_load_file(self, m_open):
        self.http_case.test_directory = '.'
        self._assert_content_read('data.json')
        m_open.assert_called_with('./data.json', mode='rb')

    def test_load_file_in_directory(self, m_open):
        self.http_case.test_directory = '.'
        self._assert_content_read('a/b/c/data.json')
        m_open.assert_called_with('./a/b/c/data.json', mode='rb')

    def test_load_file_in_root(self, m_open):
        self.http_case.test_directory = '.'
        filepath = '/top-level.private'

        with self.assertRaises(ValueError):
            self.http_case.load_data_file(filepath)
        self.assertFalse(m_open.called)

    def test_load_file_in_parent_dir(self, m_open):
        self.http_case.test_directory = '.'
        filepath = '../file-in-parent-dir.txt'

        with self.assertRaises(ValueError):
            self.http_case.load_data_file(filepath)
        self.assertFalse(m_open.called)

    def test_load_file_within_test_directory(self, m_open):
        self.http_case.test_directory = '/a/b/c'
        self._assert_content_read('../../b/c/file-in-test-dir.txt')
        m_open.assert_called_with(
            '/a/b/c/../../b/c/file-in-test-dir.txt', mode='rb')

    def test_load_file_not_within_test_directory(self, m_open):
        self.http_case.test_directory = '/a/b/c'
        filepath = '../../b/E/file-in-test-dir.txt'
        with self.assertRaises(ValueError):
            self.http_case.load_data_file(filepath)
        self.assertFalse(m_open.called)
