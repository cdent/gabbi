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
"""Test History Replacer.
"""

import sys
import unittest

from gabbi import case
from gabbi.handlers import jsonhandler
from gabbi import suitemaker


class HistoryTest(unittest.TestCase):
    """Test history variable."""

    def setUp(self):
        super(HistoryTest, self).setUp()
        self.test_class = case.HTTPTestCase
        self.test = suitemaker.TestBuilder('mytest', (self.test_class,),
                                           {'test_data': {},
                                            'content_handlers': [],
                                            'history': {},
                                            })

    def test_header_replace_prior(self):
        self.test.test_data = '$HEADERS["content-type"]'
        self.test.response = {'content-type': 'test_content'}
        self.test.prior = self.test

        header = self.test('test_request').replace_template(
            self.test.test_data)
        self.assertEqual('test_content', header)

    def test_header_replace_with_history(self):
        self.test.test_data = '$HISTORY["mytest"].$HEADERS["content-type"]'
        self.test.response = {'content-type': 'test_content'}
        self.test.history["mytest"] = self.test

        header = self.test('test_request').replace_template(
            self.test.test_data)
        self.assertEqual('test_content', header)

    def test_header_replace_with_history_regex(self):
        self.test.test_data = '/$HISTORY["mytest"].$HEADERS["content-type"]/'
        self.test.response = {'content-type': 'test+content'}
        self.test.history["mytest"] = self.test

        header = self.test('test_request').replace_template(
            self.test.test_data, escape_regex=True)
        self.assertEqual(r'/test\+content/', header)

    def test_response_replace_prior(self):
        self.test.test_data = '$RESPONSE["$.object.name"]'
        json_handler = jsonhandler.JSONHandler()
        self.test.content_type = "application/json"
        self.test.content_handlers = [json_handler]
        self.test.prior = self.test
        self.test.response = {'content-type': 'application/json'}
        self.test.response_data = {
            'object': {'name': 'test history'}
        }

        response = self.test('test_request').replace_template(
            self.test.test_data)
        self.assertEqual('test history', response)

    def test_response_replace_prior_regex(self):
        self.test.test_data = '/$RESPONSE["$.object.name"]/'
        json_handler = jsonhandler.JSONHandler()
        self.test.content_type = "application/json"
        self.test.content_handlers = [json_handler]
        self.test.prior = self.test
        self.test.response = {'content-type': 'application/json'}
        self.test.response_data = {
            'object': {'name': 'test history.'}
        }

        response = self.test('test_request').replace_template(
            self.test.test_data, escape_regex=True)
        self.assertEqual(r'/test\ history\./', response)

    def test_response_replace_with_history(self):
        self.test.test_data = '$HISTORY["mytest"].$RESPONSE["$.object.name"]'
        json_handler = jsonhandler.JSONHandler()
        self.test.content_type = "application/json"
        self.test.content_handlers = [json_handler]
        self.test.history["mytest"] = self.test
        self.test.response = {'content-type': 'application/json'}
        self.test.response_data = {
            'object': {'name': 'test history'}
        }

        response = self.test('test_request').replace_template(
            self.test.test_data)
        self.assertEqual('test history', response)

    def test_cookie_replace_prior(self):
        self.test.test_data = '$COOKIE'
        self.test.response = {'set-cookie': 'test=cookie'}
        self.test.prior = self.test

        cookie = self.test('test_request').replace_template(
            self.test.test_data)
        self.assertEqual('test=cookie', cookie)

    def test_cookie_replace_prior_regex(self):
        self.test.test_data = '/$COOKIE/'
        self.test.response = {'set-cookie': 'test=cookie?'}
        self.test.prior = self.test

        cookie = self.test('test_request').replace_template(
            self.test.test_data, escape_regex=True)
        if sys.version_info[:2] >= (3, 7):
            self.assertEqual(r'/test=cookie\?/', cookie)
        else:
            self.assertEqual(r'/test\=cookie\?/', cookie)

    def test_cookie_replace_history(self):
        self.test.test_data = '$HISTORY["mytest"].$COOKIE'
        self.test.response = {'set-cookie': 'test=cookie'}
        self.test.history["mytest"] = self.test

        cookie = self.test('test_request').replace_template(
            self.test.test_data)
        self.assertEqual('test=cookie', cookie)

    def test_location_replace_prior(self):
        self.test.test_data = '$LOCATION'
        self.test.location = 'test_location'
        self.test.prior = self.test

        location = self.test('test_request').replace_template(
            self.test.test_data)
        self.assertEqual('test_location', location)

    def test_location_replace_prior_regex(self):
        self.test.test_data = '/$LOCATION/'
        self.test.location = '..'
        self.test.prior = self.test

        location = self.test('test_request').replace_template(
            self.test.test_data, escape_regex=True)
        self.assertEqual(r'/\.\./', location)

    def test_location_replace_history(self):
        self.test.test_data = '$HISTORY["mytest"].$LOCATION'
        self.test.location = 'test_location'
        self.test.history["mytest"] = self.test

        location = self.test('test_request').replace_template(
            self.test.test_data)
        self.assertEqual('test_location', location)

    def test_url_replace_prior(self):
        self.test.test_data = '$URL'
        self.test.url = 'test_url'
        self.test.prior = self.test

        url = self.test('test_request').replace_template(
            self.test.test_data)
        self.assertEqual('test_url', url)

    def test_url_replace_prior_regex(self):
        self.test.test_data = '/$URL/'
        self.test.url = 'testurl?query'
        self.test.prior = self.test

        url = self.test('test_request').replace_template(
            self.test.test_data, escape_regex=True)
        self.assertEqual(r'/testurl\?query/', url)

    def test_url_replace_history(self):
        self.test.test_data = '$HISTORY["mytest"].$URL'
        self.test.url = 'test_url'
        self.test.history["mytest"] = self.test

        url = self.test('test_request').replace_template(
            self.test.test_data)
        self.assertEqual('test_url', url)


if __name__ == '__main__':
    unittest.main()
