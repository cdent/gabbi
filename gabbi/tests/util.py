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
"""Utility methods shared by some tests."""

import os


def set_test_environ():
    """Set some environment variables used in tests."""
    os.environ['GABBI_TEST_URL'] = 'takingnames'

    # Setup environment variables for `coerce.yaml`
    os.environ['ONE'] = '1'
    os.environ['DECIMAL'] = '1.0'
    os.environ['ARRAY_STRING'] = '[1,2,3]'
    os.environ['TRUE'] = 'true'
    os.environ['FALSE'] = 'false'
    os.environ['STRING'] = 'val'
    os.environ['NULL'] = 'null'
