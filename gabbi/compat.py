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

"""Wrappers for legacy compatibility"""

import warnings


warnings.simplefilter('default', DeprecationWarning)


def test_suite_from_yaml(loader, test_base_name, test_yaml, test_directory,
                         host, port, fixture_module, intercept, prefix=''):
    from gabbi.driver import test_suite_from_dict

    warnings.warn('test_suite_from_yaml has been renamed to '
                  'test_suite_from_dict', DeprecationWarning)
    return test_suite_from_dict(loader, test_base_name, test_yaml,
                                test_directory, host, port, fixture_module,
                                intercept, prefix)
