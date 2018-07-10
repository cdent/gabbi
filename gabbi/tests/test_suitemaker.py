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

import unittest

from gabbi import exception
from gabbi import handlers
from gabbi.handlers import yaml_disk_loading_jsonhandler as ydlj_handler
from gabbi import suitemaker


class SuiteMakerTest(unittest.TestCase):

    def setUp(self):
        super(SuiteMakerTest, self).setUp()
        self.loader = unittest.defaultTestLoader

    def test_tests_key_required(self):
        test_yaml = {'name': 'house', 'url': '/'}

        with self.assertRaises(exception.GabbiFormatError) as failure:
            suitemaker.test_suite_from_dict(self.loader, 'foo', test_yaml, '.',
                                            'localhost', 80, None, None)
        self.assertEqual('malformed test file, "tests" key required',
                         str(failure.exception))

    def test_upper_dict_required(self):
        test_yaml = [{'name': 'house', 'url': '/'}]
        with self.assertRaises(exception.GabbiFormatError) as failure:
            suitemaker.test_suite_from_dict(self.loader, 'foo', test_yaml, '.',
                                            'localhost', 80, None, None)
        self.assertEqual('malformed test file, invalid format',
                         str(failure.exception))

    def test_inner_list_required(self):
        test_yaml = {'tests': {'name': 'house', 'url': '/'}}
        with self.assertRaises(exception.GabbiFormatError) as failure:
            suitemaker.test_suite_from_dict(self.loader, 'foo', test_yaml, '.',
                                            'localhost', 80, None, None)
        self.assertIn('test chunk is not a dict at',
                      str(failure.exception))

    def test_name_key_required(self):
        test_yaml = {'tests': [{'url': '/'}]}

        with self.assertRaises(exception.GabbiFormatError) as failure:
            suitemaker.test_suite_from_dict(self.loader, 'foo', test_yaml, '.',
                                            'localhost', 80, None, None)
        self.assertEqual('Test name missing in a test in foo.',
                         str(failure.exception))

    def test_url_key_required(self):
        test_yaml = {'tests': [{'name': 'missing url'}]}

        with self.assertRaises(exception.GabbiFormatError) as failure:
            suitemaker.test_suite_from_dict(self.loader, 'foo', test_yaml, '.',
                                            'localhost', 80, None, None)
        self.assertEqual('Test url missing in test foo_missing_url.',
                         str(failure.exception))

    def test_unsupported_key_errors(self):
        test_yaml = {'tests': [{
            'url': '/',
            'name': 'simple',
            'bad_key': 'wow',
        }]}

        with self.assertRaises(exception.GabbiFormatError) as failure:
            suitemaker.test_suite_from_dict(self.loader, 'foo', test_yaml, '.',
                                            'localhost', 80, None, None)
        self.assertIn("Invalid test keys used in test foo_simple:",
                      str(failure.exception))

    def test_method_url_pair_format_error(self):
        test_yaml = {'defaults': {'GET': '/foo'}, 'tests': []}
        with self.assertRaises(exception.GabbiFormatError) as failure:
            suitemaker.test_suite_from_dict(self.loader, 'foo', test_yaml, '.',
                                            'localhost', 80, None, None)
        self.assertIn('"METHOD: url" pairs not allowed in defaults',
                      str(failure.exception))

    def test_method_url_pair_duplication_format_error(self):
        test_yaml = {'tests': [{
            'GET': '/',
            'POST': '/',
            'name': 'duplicate methods',
        }]}
        with self.assertRaises(exception.GabbiFormatError) as failure:
            suitemaker.test_suite_from_dict(self.loader, 'foo', test_yaml, '.',
                                            'localhost', 80, None, None)
        self.assertIn(
            'duplicate method/URL directive in "foo_duplicate_methods"',
            str(failure.exception)
        )

    def test_dict_on_invalid_key(self):
        test_yaml = {'tests': [{
            'name': '...',
            'GET': '/',
            'response_html': {
                'foo': 'hello',
                'bar': 'world',
            }
        }]}

        with self.assertRaises(exception.GabbiFormatError) as failure:
            suitemaker.test_suite_from_dict(self.loader, 'foo', test_yaml, '.',
                                            'localhost', 80, None, None)
        self.assertIn(
            "invalid key in test: 'response_html'",
            str(failure.exception)
        )

    def test_response_handlers_same_test_key_yaml_last(self):
        test_yaml = {'tests': [{
            'name': '...',
            'GET': '/',
            'response_json_paths': {
                'foo': 'hello',
                'bar': 'world',
            }
        }]}
        handler_objects = []
        ydlj_handler_object = ydlj_handler.YAMLDiskLoadingJSONHandler()
        for handler in handlers.RESPONSE_HANDLERS:
            handler_objects.append(handler())
        handler_objects.append(ydlj_handler_object)
        file_suite = suitemaker.test_suite_from_dict(
            self.loader, 'foo', test_yaml, '.', 'localhost', 80, None, None,
            handlers=handler_objects)
        response_handlers = file_suite._tests[0].response_handlers
        self.assertNotIn(ydlj_handler_object, response_handlers)

    def test_response_handlers_same_test_key_yaml_first(self):
        test_yaml = {'tests': [{
            'name': '...',
            'GET': '/',
            'response_json_paths': {
                'foo': 'hello',
                'bar': 'world',
            }
        }]}
        ydlj_handler_object = ydlj_handler.YAMLDiskLoadingJSONHandler()
        handler_objects = [ydlj_handler_object]
        for handler in handlers.RESPONSE_HANDLERS:
            handler_objects.append(handler())
        file_suite = suitemaker.test_suite_from_dict(
            self.loader, 'foo', test_yaml, '.', 'localhost', 80, None, None,
            handlers=handler_objects)
        response_handlers = file_suite._tests[0].response_handlers
        self.assertIn(ydlj_handler_object, response_handlers)
