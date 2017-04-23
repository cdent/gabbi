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
"""JSON-related content handling."""

import json

from gabbi.handlers import base
from gabbi import json_parser


class JSONHandler(base.ContentHandler):
    """A ContentHandler for JSON

    * Structured test ``data`` is turned into JSON when request
      content-type is JSON.
    * Response bodies that are JSON strings are made into Python
      data on the test ``response_data`` attribute when the response
      content-type is JSON.
    * A ``response_json_paths`` response handler is added.
    * JSONPaths in $RESPONSE substitutions are supported.
    """

    test_key_suffix = 'json_paths'
    test_key_value = {}

    @staticmethod
    def accepts(content_type):
        content_type = content_type.split(';', 1)[0].strip()
        return (content_type.endswith('+json') or
                content_type.startswith('application/json'))

    @classmethod
    def replacer(cls, response_data, match):
        return cls.extract_json_path_value(response_data, match)

    @staticmethod
    def dumps(data, pretty=False, test=None):
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
        # If expected is a string, check to see if it is a regex.
        if (hasattr(expected, 'startswith') and expected.startswith('/')
                and expected.endswith('/')):
            expected = expected.strip('/').rstrip('/')
            # match may be a number so stringify
            match = str(match)
            test.assertRegexpMatches(
                match, expected,
                'Expect jsonpath %s to match /%s/, got %s' %
                (path, expected, match))
        else:
            test.assertEqual(expected, match,
                             'Unable to match %s as %s, got %s' %
                             (path, expected, match))
