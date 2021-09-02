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
"""Test handling of data field in tests.
"""

import unittest

from gabbi import case
from gabbi import handlers


class TestDataToString(unittest.TestCase):

    def setUp(self):
        self.case = case.HTTPTestCase('test_request')
        self.case.content_handlers = []
        for handler in handlers.RESPONSE_HANDLERS:
            h = handler()
            if hasattr(h, 'content_handler') and h.content_handler:
                self.case.content_handlers.append(h)

    def testHappyPath(self):
        data = [{"hi": "low"}, {"yes": "no"}]
        content_type = 'application/json'
        body = self.case._test_data_to_string(data, content_type)
        self.assertEqual('[{"hi": "low"}, {"yes": "no"}]', body)

    def testNoContentType(self):
        data = [{"hi": "low"}, {"yes": "no"}]
        content_type = ''
        with self.assertRaises(ValueError) as exc:
            self.case._test_data_to_string(data, content_type)
        self.assertEqual(
            'no content-type available for processing data',
            str(exc.exception))

    def testNoHandler(self):
        data = [{"hi": "low"}, {"yes": "no"}]
        content_type = 'application/xml'
        with self.assertRaises(ValueError) as exc:
            self.case._test_data_to_string(data, content_type)
        self.assertEqual(
            'unable to process data to application/xml',
            str(exc.exception))
