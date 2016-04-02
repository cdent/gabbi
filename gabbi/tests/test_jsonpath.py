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
"""Test jsonpath handling
"""

import unittest

from gabbi.handlers import jsonhandler


extract = jsonhandler.JSONHandler.extract_json_path_value
nested_data = {
    'objects': [
        {'name': 'one', 'value': 'alpha'},
        {'name': 'two', 'value': 'beta'},
    ]
}
simple_list = {
    'objects': [
        'alpha',
        'gamma',
        'gabba',
        'hey',
        'carlton',
    ]
}


class JSONPathTest(unittest.TestCase):

    def test_basic_match(self):
        data = ['hi']
        match = extract(data, '$[0]')
        self.assertEqual('hi', match)

    def test_list_handling(self):
        data = ['hi', 'bye']
        match = extract(data, '$')
        self.assertEqual(data, match)

    def test_embedded_list_handling(self):
        match = extract(nested_data, '$.objects..name')
        self.assertEqual(['one', 'two'], match)

    def test_sorted_object_list(self):
        match = extract(nested_data, r'$.objects[\name][0].value')
        self.assertEqual('beta', match)

    def test_filtered_list(self):
        match = extract(nested_data, r'$.objects[?name = "one"].value')
        self.assertEqual('alpha', match)

    def test_sorted_simple_list(self):
        match = extract(simple_list, r'$.objects.`sorted`[-1]')
        self.assertEqual('hey', match)

    def test_len_simple_list(self):
        match = extract(simple_list, r'$.objects.`len`')
        self.assertEqual(5, match)

    def test_len_object_list(self):
        match = extract(nested_data, '$.objects.`len`')
        self.assertEqual(2, match)
