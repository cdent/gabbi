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
"""A place to put tests of URL parsing.

These verbosely cover the _parse_url method to make sure it
behaves.
"""

import unittest
import uuid

from gabbi import case


class UrlParseTest(unittest.TestCase):

    @staticmethod
    def make_test_case(host, port=8000, prefix=''):
        # Attributes used are port, prefix and host and they must
        # be set manually here, due to metaclass magics elsewhere.
        # test_data must have a base value.
        http_case = case.HTTPTestCase('test_request')
        http_case.test_data = case.BASE_TEST
        http_case.host = host
        http_case.port = port
        http_case.prefix = prefix
        return http_case

    def test_parse_url(self):
        host = uuid.uuid4()
        http_case = self.make_test_case(host)
        parsed_url = http_case._parse_url('/foobar')

        self.assertEqual('http://%s:8000/foobar' % host, parsed_url)

    def test_parse_prefix(self):
        host = uuid.uuid4()
        http_case = self.make_test_case(host, prefix='/noise')
        parsed_url = http_case._parse_url('/foobar')

        self.assertEqual('http://%s:8000/noise/foobar' % host, parsed_url)

    def test_parse_full(self):
        host = uuid.uuid4()
        http_case = self.make_test_case(host)
        parsed_url = http_case._parse_url('http://example.com/house')

        self.assertEqual('http://example.com/house', parsed_url)

    def test_with_ssl(self):
        host = uuid.uuid4().hex
        http_case = self.make_test_case(host)
        parsed_url = http_case._parse_url('/foobar', ssl=True)

        self.assertEqual('https://%s:8000/foobar' % host, parsed_url)

    def test_default_port_http(self):
        host = uuid.uuid4().hex
        http_case = self.make_test_case(host, port='80')
        parsed_url = http_case._parse_url('/foobar')

        self.assertEqual('http://%s/foobar' % host, parsed_url)

    def test_default_port_int(self):
        host = uuid.uuid4().hex
        http_case = self.make_test_case(host, port=80)
        parsed_url = http_case._parse_url('/foobar')

        self.assertEqual('http://%s/foobar' % host, parsed_url)

    def test_default_port_https(self):
        host = uuid.uuid4().hex
        http_case = self.make_test_case(host, port='443')
        parsed_url = http_case._parse_url('/foobar', ssl=True)

        self.assertEqual('https://%s/foobar' % host, parsed_url)

    def test_default_port_https_no_ssl(self):
        host = uuid.uuid4().hex
        http_case = self.make_test_case(host, port='443')
        parsed_url = http_case._parse_url('/foobar')

        self.assertEqual('http://%s:443/foobar' % host, parsed_url)

    def test_https_port_80_ssl(self):
        host = uuid.uuid4().hex
        http_case = self.make_test_case(host, port='80')
        parsed_url = http_case._parse_url('/foobar', ssl=True)

        self.assertEqual('https://%s:80/foobar' % host, parsed_url)
