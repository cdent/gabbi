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
"""Test response handlers.
"""

import json
import unittest

from gabbi import case
from gabbi.exception import GabbiFormatError
from gabbi.handlers import core
from gabbi.handlers import jsonhandler
from gabbi import suitemaker


class HandlersTest(unittest.TestCase):
    """Test the response handlers.

    Note that this does not test the magic template variables, that
    should be tested somewhere else.
    """

    def setUp(self):
        super(HandlersTest, self).setUp()
        self.test_class = case.HTTPTestCase
        self.test = suitemaker.TestBuilder('mytest', (self.test_class,),
                                           {'test_data': {},
                                           'content_handlers': []})

    def test_empty_response_handler(self):
        self.test.test_data = {'url': '$RESPONSE["barnabas"]'}
        self.test.response = {'content-type': 'unmatchable'}
        self.test.response_data = ''
        self.test.prior = self.test

        url = self.test('test_request').replace_template(
            self.test.test_data['url'])
        self.assertEqual('barnabas', url)

        self.test.response_data = None
        self.test.content_handlers = [jsonhandler.JSONHandler()]
        url = self.test('test_request').replace_template(
            self.test.test_data['url'])
        self.assertEqual('barnabas', url)

    def test_response_strings(self):
        handler = core.StringResponseHandler()
        self.test.content_type = "text/plain"
        self.test.response_data = None
        self.test.test_data = {'response_strings': ['alpha', 'beta']}
        self.test.output = 'alpha\nbeta\n'
        self._assert_handler(handler)

    def test_response_strings_fail(self):
        handler = core.StringResponseHandler()
        self.test.content_type = "text/plain"
        self.test.response_data = None
        self.test.test_data = {'response_strings': ['alpha', 'beta']}
        self.test.output = 'alpha\nbta\n'
        with self.assertRaises(AssertionError):
            self._assert_handler(handler)

    def test_response_strings_fail_big_output(self):
        handler = core.StringResponseHandler()
        self.test.content_type = "text/plain"
        self.test.response_data = None
        self.test.test_data = {'response_strings': ['alpha', 'beta']}
        self.test.output = 'alpha\nbta\n' * 1000
        with self.assertRaises(AssertionError) as cm:
            self._assert_handler(handler)

        msg = str(cm.exception)
        self.assertEqual(2036, len(msg))

    def test_response_strings_fail_big_payload(self):
        string_handler = core.StringResponseHandler()
        # Register the JSON handler so response_data is set.
        json_handler = jsonhandler.JSONHandler()
        self.test.response_handlers = [string_handler, json_handler]
        self.test.content_handlers = [json_handler]
        self.test.content_type = "application/json"
        self.test.test_data = {'response_strings': ['foobar']}
        self.test.response_data = {
            'objects': [{'name': 'cw',
                         'location': 'barn'},
                        {'name': 'chris',
                         'location': 'house'}] * 100
        }
        self.test.output = json.dumps(self.test.response_data)
        with self.assertRaises(AssertionError) as cm:
            self._assert_handler(string_handler)

        msg = str(cm.exception)
        self.assertEqual(2038, len(msg))
        # Check the pprint of the json
        self.assertIn('      "location": "house"', msg)

    def test_response_string_list_type(self):
        handler = core.StringResponseHandler()
        self.test.test_data = {
            'name': 'omega test',
            'response_strings': 'omega'
        }
        self.test.output = 'omega\n'
        with self.assertRaises(GabbiFormatError) as exc:
            self._assert_handler(handler)
            self.assertIn('has incorrect type', str(exc))
            self.assertIn("response_strings in 'omega test'",
                          str(exc))

    def test_response_json_paths(self):
        handler = jsonhandler.JSONHandler()
        self.test.content_type = "application/json"
        self.test.test_data = {'response_json_paths': {
            '$.objects[0].name': 'cow',
            '$.objects[1].location': 'house',
        }}
        self.test.response_data = {
            'objects': [{'name': 'cow',
                         'location': 'barn'},
                        {'name': 'chris',
                         'location': 'house'}]
        }
        self._assert_handler(handler)

    def test_response_json_paths_fail_data(self):
        handler = jsonhandler.JSONHandler()
        self.test.content_type = "application/json"
        self.test.test_data = {'response_json_paths': {
            '$.objects[0].name': 'cow',
            '$.objects[1].location': 'house',
        }}
        self.test.response_data = {
            'objects': [{'name': 'cw',
                         'location': 'barn'},
                        {'name': 'chris',
                         'location': 'house'}]
        }
        with self.assertRaises(AssertionError):
            self._assert_handler(handler)

    def test_response_json_paths_fail_path(self):
        handler = jsonhandler.JSONHandler()
        self.test.content_type = "application/json"
        self.test.test_data = {'response_json_paths': {
            '$.objects[1].name': 'cow',
        }}
        self.test.response_data = {
            'objects': [{'name': 'cow',
                         'location': 'barn'},
                        {'name': 'chris',
                         'location': 'house'}]
        }
        with self.assertRaises(AssertionError):
            self._assert_handler(handler)

    def test_response_json_paths_regex(self):
        handler = jsonhandler.JSONHandler()
        self.test.content_type = "application/json"
        self.test.test_data = {'response_json_paths': {
            '$.objects[0].name': '/ow/',
        }}
        self.test.response_data = {
            'objects': [{'name': 'cow',
                         'location': 'barn'},
                        {'name': 'chris',
                         'location': 'house'}]
        }
        self._assert_handler(handler)

    def test_response_json_paths_regex_number(self):
        handler = jsonhandler.JSONHandler()
        self.test.content_type = "application/json"
        self.test.test_data = {'response_json_paths': {
            '$.objects[0].name': '/\d+/',
        }}
        self.test.response_data = {
            'objects': [{'name': 99,
                         'location': 'barn'},
                        {'name': 'chris',
                         'location': 'house'}]
        }
        self._assert_handler(handler)

    def test_response_json_paths_dict_type(self):
        handler = jsonhandler.JSONHandler()
        self.test.test_data = {
            'name': 'omega test',
            'response_json_paths': ['alpha', 'beta']
        }
        self.test.output = 'omega\n'
        with self.assertRaises(GabbiFormatError) as exc:
            self._assert_handler(handler)
            self.assertIn('has incorrect type', str(exc))
            self.assertIn("response_json_paths in 'omega test'",
                          str(exc))

    def test_response_headers(self):
        handler = core.HeadersResponseHandler()
        self.test.response = {'content-type': 'text/plain'}

        self.test.test_data = {'response_headers': {
            'content-type': 'text/plain',
        }}
        self._assert_handler(handler)

        self.test.test_data = {'response_headers': {
            'Content-Type': 'text/plain',
        }}
        self._assert_handler(handler)

    def test_response_headers_regex(self):
        handler = core.HeadersResponseHandler()
        self.test.test_data = {'response_headers': {
            'content-type': '/text/plain/',
        }}
        self.test.response = {'content-type': 'text/plain; charset=UTF-8'}
        self._assert_handler(handler)

    def test_response_headers_fail_data(self):
        handler = core.HeadersResponseHandler()
        self.test.test_data = {'response_headers': {
            'content-type': 'text/plain',
        }}
        self.test.response = {'content-type': 'application/json'}
        with self.assertRaises(AssertionError) as failure:
            self._assert_handler(handler)
        self.assertIn("Expect header content-type with value text/plain,"
                      " got application/json",
                      str(failure.exception))

    def test_response_headers_fail_header(self):
        handler = core.HeadersResponseHandler()
        self.test.test_data = {'response_headers': {
            'location': '/somewhere',
        }}
        self.test.response = {'content-type': 'application/json'}
        with self.assertRaises(AssertionError) as failure:
            self._assert_handler(handler)
        self.assertIn("'location' header not present in response:",
                      str(failure.exception))

    def test_resonse_headers_stringify(self):
        handler = core.HeadersResponseHandler()
        self.test.test_data = {'response_headers': {
            'x-alpha-beta': 2.0,
        }}
        self.test.response = {'x-alpha-beta': '2.0'}
        self._assert_handler(handler)

        self.test.response = {'x-alpha-beta': 2.0}
        self._assert_handler(handler)

    def _assert_handler(self, handler):
        # Instantiate our contained test class by naming its test
        # method and then run its tests to confirm.
        test = self.test('test_request')
        handler(test)
