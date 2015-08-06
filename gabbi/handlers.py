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
"""Handlers for processing the body of a response in various ways.

A response handler is a class that adds functionality for making assertions
about an HTTP response.

A subclass may implement two methods: ``action`` and ``preprocess``.

``preprocess`` takes one argument, the ``TestCase``. It is called exactly
once for each test before looping across the assertions. It is used, rarely,
to copy the ``test.output`` into a useful form (such as a parsed DOM).

``action`` takes two or three arguments. If ``test_key_value`` is a list
``action`` is called with the test case and a single list item. If
``test_key_value`` is a dict then ``action`` is called with the test case
and a key and value pair.
"""


class ResponseHandler(object):

    test_key_suffix = ''
    test_key_value = []

    def __init__(self, test_class):
        self._key = 'response_%s' % self.test_key_suffix
        self._register(test_class)

    def __call__(self, test):
        if test.test_data[self._key]:
            self.preprocess(test)
            for item in test.test_data[self._key]:
                try:
                    value = test.test_data[self._key][item]
                except (TypeError, KeyError):
                    value = None
                self.action(test, item, value=value)

    def preprocess(self, test):
        """Do any pre-single-test preprocessing."""
        pass

    def action(self, test, item, value=None):
        """Test an individual entry for this response handler.

        If the entry is a key value pair the key is in item and the
        value in value. Otherwise the entry is considered a single item
        from a list.
        """
        pass

    def _register(self, test_class):
        test_class.base_test[self._key] = self.test_key_value
        if self not in test_class.response_handlers:
            test_class.response_handlers.append(self)

    def __eq__(self, other):
        if isinstance(other, ResponseHandler):
            return self.__class__ == other.__class__
        return False

    def __ne__(self, other):
        return (not self.__eq__(other))


class StringResponseHandler(ResponseHandler):
    """Test for matching strings in the the response body."""

    test_key_suffix = 'strings'
    test_key_value = []

    def action(self, test, expected, value=None):
        expected = test.replace_template(expected)
        test.assert_in_or_print_output(expected, test.output)


class JSONResponseHandler(ResponseHandler):
    """Test for matching json paths in the json_data."""

    test_key_suffix = 'json_paths'
    test_key_value = {}

    def action(self, test, path, value):
        """Test json_paths against json data."""
        # NOTE: This process has some advantages over other process that
        # might come along because the JSON data has already been
        # processed (to provided for the magic template replacing).
        # Other handlers that want access to data structures will need
        # to do their own processing.
        try:
            match = test.extract_json_path_value(test.json_data, path)
        except AttributeError:
            raise AssertionError('unable to extract JSON from test results')
        except ValueError:
            raise AssertionError('json path %s cannot match %s' %
                                 (path, test.json_data))
        expected = test.replace_template(value)
        test.assertEqual(expected, match, 'Unable to match %s as %s, got %s'
                         % (path, expected, match))


class HeadersResponseHandler(ResponseHandler):
    """Compare expected headers with actual headers.

    If a header value is wrapped in ``/`` it is treated as a raw
    regular expression.
    """

    test_key_suffix = 'headers'
    test_key_value = {}

    def action(self, test, header, value):
        header = header.lower()  # case-insensitive comparison

        response = test.response
        header_value = test.replace_template(value)

        try:
            response_value = response[header]
        except KeyError:
            raise AssertionError(
                "'%s' header not present in response: %s" % (
                    header, response.keys()))

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
