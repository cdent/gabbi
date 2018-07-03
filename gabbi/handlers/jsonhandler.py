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

import six

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
    def load_data_file(test, file_path):
        info = test.load_data_file(file_path)
        info = six.text_type(info, 'UTF-8')
        return json.loads(info)

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
        # Do template expansion in the left hand side.
        lhs_path = test.replace_template(path)
        rhs_path = rhs_match = None
        try:
            lhs_match = self.extract_json_path_value(
                test.response_data, lhs_path)
        except AttributeError:
            raise AssertionError('unable to extract JSON from test results')
        except ValueError:
            raise AssertionError('left hand side json path %s cannot match '
                                 '%s' % (path, test.response_data))

        # read data from disk if the value starts with '<@'
        if isinstance(value, six.string_types) and value.startswith('<@'):
            # Do template expansion in the rhs if rhs_path is provided.
            if ':' in value:
                value, rhs_path = value.split(':$', 1)
                rhs_path = test.replace_template('$' + rhs_path)
            value = self.load_data_file(test, value.replace('<@', '', 1))
            if rhs_path:
                try:
                    rhs_match = self.extract_json_path_value(value, rhs_path)
                except AttributeError:
                    raise AssertionError('unable to extract JSON from data on '
                                         'disk')
                except ValueError:
                    raise AssertionError('right hand side json path %s cannot '
                                         'match %s' % (rhs_path, value))

        # If expected is a string, check to see if it is a regex.
        is_regex = (isinstance(value, six.string_types) and
                    value.startswith('/') and
                    value.endswith('/') and
                    len(value) > 1)
        expected = (rhs_match or
                    test.replace_template(value, escape_regex=is_regex))
        match = lhs_match
        if is_regex and not rhs_match:
            expected = expected[1:-1]
            # match may be a number so stringify
            match = six.text_type(match)
            test.assertRegex(
                match, expected,
                'Expect jsonpath %s to match /%s/, got %s' %
                (path, expected, match))
        else:
            test.assertEqual(expected, match,
                             'Unable to match %s as %s, got %s' %
                             (path, expected, match))
