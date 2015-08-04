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
