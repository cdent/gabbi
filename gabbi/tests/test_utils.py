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
"""Test functions from the utils module.
"""

import unittest

from gabbi import utils


class UtilsTest(unittest.TestCase):

    BINARY_TYPES = [
        'image/png',
        'application/binary',
    ]

    NON_BINARY_TYPES = [
        'text/plain',
        'application/atom+xml',
        'application/vnd.custom+json',
        'application/javascript',
        'application/json',
        'application/json-home',
    ]

    def test_not_binary(self):
        for media_type in self.NON_BINARY_TYPES:
            self.assertTrue(utils.not_binary(media_type),
                            '%s should not be binary' % media_type)

    def test_binary(self):
        for media_type in self.BINARY_TYPES:
            self.assertFalse(utils.not_binary(media_type),
                             '%s should be binary' % media_type)

    def test_extract_content_type_default_both(self):
        """Empty dicts returns default type and chartset."""
        content_type, charset = utils.extract_content_type({})

        self.assertEqual('application/binary', content_type)
        self.assertEqual('utf-8', charset)

    def test_extract_content_type_default_charset(self):
        """Empty dicts returns default type and chartset."""
        content_type, charset = utils.extract_content_type({
            'content-type': 'text/colorful'})

        self.assertEqual('text/colorful', content_type)
        self.assertEqual('utf-8', charset)

    def test_extract_content_type_with_charset(self):
        content_type, charset = utils.extract_content_type(
            {'content-type': 'text/colorful; charset=latin-10'})

        self.assertEqual('text/colorful', content_type)
        self.assertEqual('latin-10', charset)

    def test_extract_content_type_multiple_params(self):
        content_type, charset = utils.extract_content_type(
            {'content-type': 'text/colorful; version=1.24; charset=latin-10'})

        self.assertEqual('text/colorful', content_type)
        self.assertEqual('latin-10', charset)

    def test_extract_content_type_bad_params(self):
        content_type, charset = utils.extract_content_type(
            {'content-type': 'text/colorful; version=1.24; charset=latin-10;'})

        self.assertEqual('text/colorful', content_type)
        self.assertEqual('utf-8', charset)

    def test__colorize_missing_color(self):
        """Make sure that choosing a non-existent color is safe."""
        message = utils._colorize('CERULEAN', 'hello')
        self.assertEqual('hello', message)

        message = utils._colorize('BLUE', 'hello')
        self.assertNotEqual('hello', message)
