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
from gabbi import driver
from gabbi import handlers
from gabbi.handlers import jsonhandler
from gabbi.tests import html_content_handler


class HandlersTest(unittest.TestCase):
    """Test the response handlers.

    Note that this does not test the magic template variables, that
    should be tested somewhere else.
    """

    def setUp(self):
        super(HandlersTest, self).setUp()
        # clear handlers before each test run
        case.HTTPTestCase.response_handlers = []
        case.HTTPTestCase.content_handlers = []
        case.HTTPTestCase.base_test = case.BASE_TEST
        self.test_class = case.HTTPTestCase
        self.test = driver.TestBuilder('mytest', (self.test_class,),
                                       {'test_data': {}})

    def test_response_strings(self):
        handler = handlers.StringResponseHandler(self.test_class)
        self.test.content_type = "text/plain"
        self.test.response_data = None
        self.test.test_data = {'response_strings': ['alpha', 'beta']}
        self.test.output = 'alpha\nbeta\n'
        self._assert_handler(handler)

    def test_response_strings_fail(self):
        handler = handlers.StringResponseHandler(self.test_class)
        self.test.content_type = "text/plain"
        self.test.response_data = None
        self.test.test_data = {'response_strings': ['alpha', 'beta']}
        self.test.output = 'alpha\nbta\n'
        with self.assertRaises(AssertionError):
            self._assert_handler(handler)

    def test_response_strings_fail_big_output(self):
        handler = handlers.StringResponseHandler(self.test_class)
        self.test.content_type = "text/plain"
        self.test.response_data = None
        self.test.test_data = {'response_strings': ['alpha', 'beta']}
        self.test.output = 'alpha\nbta\n' * 1000
        with self.assertRaises(AssertionError) as cm:
            self._assert_handler(handler)

        msg = str(cm.exception)
        self.assertEqual(2036, len(msg))

    def test_response_strings_fail_big_payload(self):
        handler = handlers.StringResponseHandler(self.test_class)
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
            self._assert_handler(handler)

        msg = str(cm.exception)
        self.assertEqual(2038, len(msg))
        # Check the pprint of the json
        self.assertIn('      "location": "house"', msg)

    def test_response_json_paths(self):
        handler = jsonhandler.JSONHandler(self.test_class)
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
        handler = jsonhandler.JSONHandler(self.test_class)
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
        handler = jsonhandler.JSONHandler(self.test_class)
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

    def test_response_headers(self):
        handler = handlers.HeadersResponseHandler(self.test_class)
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
        handler = handlers.HeadersResponseHandler(self.test_class)
        self.test.test_data = {'response_headers': {
            'content-type': '/text/plain/',
        }}
        self.test.response = {'content-type': 'text/plain; charset=UTF-8'}
        self._assert_handler(handler)

    def test_response_headers_fail_data(self):
        handler = handlers.HeadersResponseHandler(self.test_class)
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
        handler = handlers.HeadersResponseHandler(self.test_class)
        self.test.test_data = {'response_headers': {
            'location': '/somewhere',
        }}
        self.test.response = {'content-type': 'application/json'}
        with self.assertRaises(AssertionError) as failure:
            self._assert_handler(handler)
        self.assertIn("'location' header not present in response:",
                      str(failure.exception))

    def test_resonse_headers_stringify(self):
        handler = handlers.HeadersResponseHandler(self.test_class)
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


class TestHTMLContentHandler(unittest.TestCase):

    def setUp(self):
        super(TestHTMLContentHandler, self).setUp()
        # clear handlers before each test run
        case.HTTPTestCase.response_handlers = []
        case.HTTPTestCase.content_handlers = []
        case.HTTPTestCase.base_test = case.BASE_TEST
        self.test_class = case.HTTPTestCase
        self.test = driver.TestBuilder('mytest', (self.test_class,),
                                       {'test_data': {}})
        self.handler_class = html_content_handler.HTMLHandler
        self.handler = self.handler_class(self.test_class)

    def test_data(self):
        form_data = dict(name='foo', cat='thom', choices=['alpha', 'beta'])
        form_string = self.handler_class.dumps(form_data)
        self.assertIn('cat=thom', form_string)
        self.assertIn('choices=alpha', form_string)
        self.assertIn('choices=beta', form_string)
        self.assertIn('name=foo', form_string)

    def test_loads(self):
        self.test.output = '<html><body><h1>Hi</h1></html>'
        response_data = self.handler_class.loads(self.test.output)
        node = response_data.cssselect('h1')
        self.assertEqual('Hi', node[0].text)
