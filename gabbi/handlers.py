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


def handle_response_strings(test):
    """Compare strings in response body."""
    for expected in test.test_data['response_strings']:
        expected = test.replace_template(expected)
        test.assertIn(expected, test.output)


def handle_json_paths(test):
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
