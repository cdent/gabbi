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


class BinaryTypesTest(unittest.TestCase):

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


class ExtractContentTypeTest(unittest.TestCase):

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


class ColorizeTest(unittest.TestCase):

    def test_colorize_missing_color(self):
        """Make sure that choosing a non-existent color is safe."""
        message = utils._colorize('CERULEAN', 'hello')
        self.assertEqual('hello', message)

        message = utils._colorize('BLUE', 'hello')
        self.assertNotEqual('hello', message)


class CreateURLTest(unittest.TestCase):

    def test_create_url_simple(self):
        url = utils.create_url('/foo/bar', 'test.host.com')
        self.assertEqual('http://test.host.com/foo/bar', url)

    def test_create_url_ssl(self):
        url = utils.create_url('/foo/bar', 'test.host.com', ssl=True)
        self.assertEqual('https://test.host.com/foo/bar', url)

    def test_create_url_prefix(self):
        url = utils.create_url('/foo/bar', 'test.host.com', prefix='/zoom')
        self.assertEqual('http://test.host.com/zoom/foo/bar', url)

    def test_create_url_port(self):
        url = utils.create_url('/foo/bar', 'test.host.com', port=8000)
        self.assertEqual('http://test.host.com:8000/foo/bar', url)

    def test_create_url_port_and_ssl(self):
        url = utils.create_url('/foo/bar', 'test.host.com', ssl=True,
                               port=8000)
        self.assertEqual('https://test.host.com:8000/foo/bar', url)

    def test_create_url_not_ssl_on_443(self):
        url = utils.create_url('/foo/bar', 'test.host.com', ssl=False,
                               port=443)
        self.assertEqual('http://test.host.com:443/foo/bar', url)

    def test_create_url_ssl_on_80(self):
        url = utils.create_url('/foo/bar', 'test.host.com', ssl=True,
                               port=80)
        self.assertEqual('https://test.host.com:80/foo/bar', url)

    def test_create_url_preserve_query(self):
        url = utils.create_url('/foo/bar?x=1&y=2', 'test.host.com', ssl=True,
                               port=80)
        self.assertEqual('https://test.host.com:80/foo/bar?x=1&y=2', url)
