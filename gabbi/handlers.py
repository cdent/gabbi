# Copyright 2014, 2015 Red Hat
#
# Authors: Chris Dent <chdent@redhat.com>
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
"""Handlers for process the body of a response in various ways.

A response handler is a callable that takes a test case (which includes
a reference to the response body). It should look for matching rules in
the test data and simply return if none are there. If there are some,
they should be tested.
"""


class ResponseHandler(object):

    test_key_suffix = ''
    test_key_value = []

    def __init__(self, test_class):
        self._register(test_class)

    def __call__(self, test):
        pass

    def _register(self, test_class):
        test_key = 'response_%s' % self.test_key_suffix
        test_class.base_test[test_key] = self.test_key_value
        test_class.response_handlers.append(self)


class StringResponseHandler(ResponseHandler):

    test_key_suffix = 'strings'
    test_key_value = []

    def __call__(self, test):
        """Compare strings in response body."""
        for expected in test.test_data['response_strings']:
            expected = test.replace_template(expected)
            test.assertIn(expected, test.output)


class JSONResponseHandler(ResponseHandler):

    test_key_suffix = 'json_paths'
    test_key_value = {}

    def __call__(self, test):
        """Test json_paths against json data."""
        # NOTE: This process has some advantages over other process that
        # might come along because the JSON data has already been
        # processed (to provided for the magic template replacing).
        # Other handlers that want access to data structures will need
        # to do their own processing.
        for path in test.test_data['response_json_paths']:
            match = test.extract_json_path_value(test.json_data, path)
            expected = test.replace_template(
                test.test_data['response_json_paths'][path])
            test.assertEqual(expected, match, 'Unable to match %s as %s'
                             % (path, expected))


class HeadersResponseHandler(ResponseHandler):

    test_key_suffix = 'headers'
    test_key_value = {}

    def __call__(self, test):
        """Compare expected headers with actual headers.

        If a header value is wrapped in ``/`` it is treated as a raw
        regular expression.
        """
        headers = test.test_data['response_headers']
        response = test.response

        for header in headers:
            header_value = test.replace_template(headers[header])

            try:
                response_value = response[header]
            except KeyError:
                # Reform KeyError to something more debuggable.
                raise KeyError("'%s' header not available in response keys: %s"
                               % (header, response.keys()))

            if header_value.startswith('/') and header_value.endswith('/'):
                header_value = header_value.strip('/').rstrip('/')
                test.assertRegexpMatches(
                    response_value, header_value,
                    'Expect header %s to match /%s/, got %s' %
                    (header, header_value, response_value))
            else:
                test.assertEqual(header_value, response[header],
                                 'Expect header %s with value %s, got %s' %
                                 (header, header_value, response[header]))
