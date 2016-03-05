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
"""Extend jsonpath_rw to add a len command."""

import functools

import jsonpath_rw
from jsonpath_rw_ext import _iterable
from jsonpath_rw_ext import parser


PARSER = None


def custom_find(self, datum):
    """Return sorted value of This if list or dict."""
    if isinstance(datum.value, dict) and self.expressions:
        return datum

    if isinstance(datum.value, dict) or isinstance(datum.value, list):
        key = (functools.cmp_to_key(self._compare)
               if self.expressions else None)
        return [jsonpath_rw.DatumInContext.wrap(
            [value for value in sorted(datum.value, key=key)])]
    return datum


# Override jsonpath_pw_ext return from find so we have the right
# data structure. Monkey patch because there are too many places to
# change in the lexer and parser.
_iterable.SortedThis.find = custom_find


def parse(path):
    global PARSER
    if not PARSER:
        PARSER = parser.ExtentedJsonPathParser()
    return PARSER.parse(path)
