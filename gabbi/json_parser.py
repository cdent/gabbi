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
"""Keep one single global jsonpath parser."""

from jsonpath_rw_ext import parser


PARSER = None


def parse(path):
    """Parse a JSONPath expression use the global parser."""
    global PARSER
    if not PARSER:
        PARSER = parser.ExtentedJsonPathParser()
    return PARSER.parse(path)
