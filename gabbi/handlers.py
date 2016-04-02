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
"""Handlers for processing the body of a response in various ways."""

import json

from gabbi import json_parser


class ResponseHandler(object):
    """Add functionality for making assertions about an HTTP response.

    A subclass may implement two methods: ``action`` and ``preprocess``.

    ``preprocess`` takes one argument, the ``TestCase``. It is called exactly
    once for each test before looping across the assertions. It is used,
    rarely, to copy the ``test.output`` into a useful form (such as a parsed
    DOM).

    ``action`` takes two or three arguments. If ``test_key_value`` is a list
    ``action`` is called with the test case and a single list item. If
    ``test_key_value`` is a dict then ``action`` is called with the test case
    and a key and value pair.
    """

    test_key_suffix = ''
    test_key_value = []

    def __init__(self, test_class):
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
        """Register this handler on the provided test class."""
        if self.test_key_suffix:
            self._key = 'response_%s' % self.test_key_suffix
            test_class.base_test[self._key] = self.test_key_value
            if self not in test_class.response_handlers:
                test_class.response_handlers.append(self)
        if hasattr(self, 'accepts'):
            if self not in test_class.content_handlers:
                test_class.content_handlers.append(self)

    def __eq__(self, other):
        if isinstance(other, ResponseHandler):
            return self.__class__ == other.__class__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class StringResponseHandler(ResponseHandler):
    """Test for matching strings in the the response body."""

    test_key_suffix = 'strings'
    test_key_value = []

    def action(self, test, expected, value=None):
        expected = test.replace_template(expected)
        test.assert_in_or_print_output(expected, test.output)


class ForbiddenHeadersResponseHandler(ResponseHandler):
    """Test that listed headers are not in the response."""

    test_key_suffix = 'forbidden_headers'
    test_key_value = []

    def action(self, test, forbidden, value=None):
        # normalize forbidden header to lower case
        forbidden = test.replace_template(forbidden).lower()
        test.assertNotIn(forbidden, test.response,
                         'Forbidden header %s found in response' % forbidden)


class HeadersResponseHandler(ResponseHandler):
    """Compare expected headers with actual headers.

    If a header value is wrapped in ``/`` it is treated as a raw
    regular expression.

    Headers values are always treated as strings.
    """

    test_key_suffix = 'headers'
    test_key_value = {}

    def action(self, test, header, value=None):
        header = header.lower()  # case-insensitive comparison

        response = test.response
        header_value = test.replace_template(str(value))

        try:
            response_value = str(response[header])
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
            test.assertEqual(header_value, response_value,
                             'Expect header %s with value %s, got %s' %
                             (header, header_value, response[header]))


class ContentHandler(object):
    """A mixin for ResponseHandlers that add content handling."""

    @staticmethod
    def accepts(content_type):
        """Return True if this handler can handler this type."""
        return False

    @staticmethod
    def gen_replacer(test):
        """Return a function which does RESPONSE replacing."""
        def replacer_func(match):
            return match.group('arg')
        return replacer_func

    @staticmethod
    def dumps(data, pretty=False):
        """Return structured data as a string.

        If pretty is true, prettify.
        """
        return data

    @staticmethod
    def loads(data):
        """Create structured (Python) data from a stream."""
        return data


class JSONHandler(ResponseHandler, ContentHandler):

    test_key_suffix = 'json_paths'
    test_key_value = {}

    @staticmethod
    def accepts(content_type):
        content_type = content_type.split(';', 1)[0].strip()
        return (content_type.endswith('+json') or
                content_type.startswith('application/json'))

    @classmethod
    def gen_replacer(cls, test):
        def replacer_func(match):
            path = match.group('arg')
            return str(cls.extract_json_path_value(
                test.prior.response_data, path))
        return replacer_func

    @staticmethod
    def dumps(data, pretty=False):
        if pretty:
            return json.dumps(data, indent=2, separators=(',', ': '))
        else:
            return json.dumps(data)

    @staticmethod
    def loads(data):
        return json.loads(data)

    @staticmethod
    def extract_json_path_value(data, path):
        """Extract the value at JSON Path path from the data.

        The input data is a Python datastructure, not a JSON string.
        """
        path_expr = json_parser.parse(path)
        matches = [match.value for match in path_expr.find(data)]
        if matches:
            if len(matches) > 1:
                return matches
            else:
                return matches[0]
        else:
            raise ValueError(
                "JSONPath '%s' failed to match on data: '%s'" % (path, data))

    def action(self, test, path, value=None):
        """Test json_paths against json data."""
        # NOTE: This process has some advantages over other process that
        # might come along because the JSON data has already been
        # processed (to provided for the magic template replacing).
        # Other handlers that want access to data structures will need
        # to do their own processing.
        try:
            match = self.extract_json_path_value(
                test.response_data, path)
        except AttributeError:
            raise AssertionError('unable to extract JSON from test results')
        except ValueError:
            raise AssertionError('json path %s cannot match %s' %
                                 (path, test.response_data))
        expected = test.replace_template(value)
        test.assertEqual(expected, match, 'Unable to match %s as %s, got %s'
                         % (path, expected, match))
