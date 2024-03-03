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
"""Core response handlers."""

from gabbi.handlers import base


class StringResponseHandler(base.ResponseHandler):
    """Test for matching strings in the the response body."""

    test_key_suffix = 'strings'
    test_key_value = []

    def action(self, test, expected, value=None):
        is_regex = self.is_regex(expected)
        expected = test.replace_template(expected, escape_regex=is_regex)

        if is_regex:
            # Trim off /
            expected = expected[1:-1]
            test.assertRegex(
                test.output, expected,
                'Expect resonse body %s to match /%s/' %
                (test.output, expected))
        else:
            test.assert_in_or_print_output(expected, test.output)


class ForbiddenHeadersResponseHandler(base.ResponseHandler):
    """Test that listed headers are not in the response."""

    test_key_suffix = 'forbidden_headers'
    test_key_value = []

    def action(self, test, forbidden, value=None):
        # normalize forbidden header to lower case
        forbidden = test.replace_template(forbidden).lower()
        test.assertNotIn(forbidden, test.response,
                         'Forbidden header %s found in response' % forbidden)


class HeadersResponseHandler(base.ResponseHandler):
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

        header_value = str(value)
        is_regex = self.is_regex(header_value)
        header_value = test.replace_template(header_value,
                                             escape_regex=is_regex)

        try:
            response_value = str(response[header])
        except KeyError:
            raise AssertionError(
                "'%s' header not present in response: %s" % (
                    header, response.keys()))

        if is_regex:
            header_value = header_value[1:-1]
            test.assertRegex(
                response_value, header_value,
                'Expect header %s to match /%s/, got %s' %
                (header, header_value, response_value))
        else:
            test.assertEqual(header_value, response_value,
                             'Expect header %s with value %s, got %s' %
                             (header, header_value, response[header]))
