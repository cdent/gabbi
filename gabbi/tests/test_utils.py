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
        'application/xml',
    ]

    def test_not_binary(self):
        for media_type in self.NON_BINARY_TYPES:
            self.assertTrue(utils.not_binary(media_type),
                            '%s should not be binary' % media_type)

    def test_binary(self):
        for media_type in self.BINARY_TYPES:
            self.assertFalse(utils.not_binary(media_type),
                             '%s should be binary' % media_type)


class ParseContentTypeTest(unittest.TestCase):

    def test_parse_simple(self):
        self.assertEqual(
            ('text/plain', 'latin-1'),
            utils.parse_content_type('text/plain; charset=latin-1'))

    def test_parse_extra(self):
        self.assertEqual(
            ('text/plain', 'latin-1'),
            utils.parse_content_type(
                'text/plain; charset=latin-1; version=1.2'))

    def test_parse_default(self):
        self.assertEqual(
            ('text/plain', 'utf-8'),
            utils.parse_content_type('text/plain'))

    def test_parse_error_default(self):
        self.assertEqual(
            ('text/plain', 'utf-8'),
            utils.parse_content_type(
                'text/plain; face=ouch; charset=latin-1;'))

    def test_parse_nocharset_default(self):
        self.assertEqual(
            ('text/plain', 'utf-8'),
            utils.parse_content_type(
                'text/plain; face=ouch'))

    def test_parse_override_default(self):
        self.assertEqual(
            ('text/plain', 'latin-1'),
            utils.parse_content_type(
                'text/plain; face=ouch', default_charset='latin-1'))


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

    def test_create_url_ipv6_ssl(self):
        url = utils.create_url('/foo/bar?x=1&y=2', '::1', ssl=True)
        self.assertEqual('https://[::1]/foo/bar?x=1&y=2', url)

    def test_create_url_ipv6_ssl_weird_port(self):
        url = utils.create_url('/foo/bar?x=1&y=2', '::1', ssl=True, port=80)
        self.assertEqual('https://[::1]:80/foo/bar?x=1&y=2', url)

    def test_create_url_ipv6_full(self):
        url = utils.create_url('/foo/bar?x=1&y=2',
                               '2607:f8b0:4000:801::200e', port=8080)
        self.assertEqual(
            'http://[2607:f8b0:4000:801::200e]:8080/foo/bar?x=1&y=2', url)

    def test_create_url_ipv6_already_bracket(self):
        url = utils.create_url(
            '/foo/bar?x=1&y=2', '[2607:f8b0:4000:801::200e]', port=999)
        self.assertEqual(
            'http://[2607:f8b0:4000:801::200e]:999/foo/bar?x=1&y=2', url)

    def test_create_url_no_double_colon(self):
        url = utils.create_url(
            '/foo', 'FEDC:BA98:7654:3210:FEDC:BA98:7654:3210', port=999)
        self.assertEqual(
            'http://[FEDC:BA98:7654:3210:FEDC:BA98:7654:3210]:999/foo', url)


class UtilsHostInfoFromTarget(unittest.TestCase):

    def _test_hostport(self, url_or_host, expected_host,
                       provided_prefix=None, expected_port=None,
                       expected_prefix='', expected_ssl=False):
        host, port, prefix, ssl = utils.host_info_from_target(
            url_or_host, provided_prefix)

        # normalize hosts, they are case insensitive
        self.assertEqual(expected_host.lower(), host.lower())
        # port can be a string or int depending on the inputs
        self.assertEqual(str(expected_port), str(port))
        self.assertEqual(expected_prefix, prefix)
        self.assertEqual(expected_ssl, ssl)

    def test_plain_url_no_port(self):
        self._test_hostport('http://foobar.com/news',
                            'foobar.com',
                            expected_port=None,
                            expected_prefix='/news')

    def test_plain_url_with_port(self):
        self._test_hostport('http://foobar.com:80/news',
                            'foobar.com',
                            expected_port=80,
                            expected_prefix='/news')

    def test_ssl_url(self):
        self._test_hostport('https://foobar.com/news',
                            'foobar.com',
                            expected_prefix='/news',
                            expected_ssl=True)

    def test_ssl_port80_url(self):
        self._test_hostport('https://foobar.com:80/news',
                            'foobar.com',
                            expected_prefix='/news',
                            expected_port=80,
                            expected_ssl=True)

    def test_ssl_port_url(self):
        self._test_hostport('https://foobar.com:999/news',
                            'foobar.com',
                            expected_prefix='/news',
                            expected_port=999,
                            expected_ssl=True)

    def test_simple_hostport(self):
        self._test_hostport('foobar.com:999',
                            'foobar.com',
                            expected_port='999')

    def test_simple_hostport_with_prefix(self):
        self._test_hostport('foobar.com:999',
                            'foobar.com',
                            provided_prefix='/news',
                            expected_port='999',
                            expected_prefix='/news')

    def test_ipv6_url_long(self):
        self._test_hostport(
            'http://[FEDC:BA98:7654:3210:FEDC:BA98:7654:3210]:999/news',
            'FEDC:BA98:7654:3210:FEDC:BA98:7654:3210',
            expected_port=999,
            expected_prefix='/news')

    def test_ipv6_url_localhost(self):
        self._test_hostport(
            'http://[::1]:999/news',
            '::1',
            expected_port=999,
            expected_prefix='/news')

    def test_ipv6_host_localhost(self):
        # If a user wants to use the hostport form, then they need
        # to hack it with the brackets.
        self._test_hostport(
            '[::1]',
            '::1')

    def test_ipv6_hostport_localhost(self):
        self._test_hostport(
            '[::1]:999',
            '::1',
            expected_port='999')
