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
"""A place to put test of the replacers.
"""

import os

import unittest

from gabbi import case


class EnvironReplaceTest(unittest.TestCase):

    def test_environ_boolean(self):
        """Environment variables are always strings

        That doesn't always suit our purposes, so test that "True"
        and "False" become booleans as a special case.
        """
        http_case = case.HTTPTestCase('test_request')
        message = "$ENVIRON['moo']"

        os.environ['moo'] = "True"
        self.assertEqual(True, http_case._environ_replace(message))

        os.environ['moo'] = "False"
        self.assertEqual(False, http_case._environ_replace(message))

        os.environ['moo'] = "true"
        self.assertEqual(True, http_case._environ_replace(message))

        os.environ['moo'] = "faLse"
        self.assertEqual(False, http_case._environ_replace(message))

        os.environ['moo'] = "null"
        self.assertEqual(None, http_case._environ_replace(message))

        os.environ['moo'] = "1"
        self.assertEqual(1, http_case._environ_replace(message))

        os.environ['moo'] = "cow"
        self.assertEqual("cow", http_case._environ_replace(message))

        message = '$ENVIRON["moo"]'

        os.environ['moo'] = "True"
        self.assertEqual(True, http_case._environ_replace(message))
