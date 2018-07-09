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
"""JSON-related content handling with YAML data disk loading."""

import yaml

import six

from gabbi.handlers import jsonhandler


class YAMLDiskLoadingJSONHandler(jsonhandler.JSONHandler):
    """A ContentHandler for JSON responses that loads YAML from disk

    * Structured test ``data`` is turned into JSON when request
      content-type is JSON.
    * Response bodies that are JSON strings are made into Python
      data on the test ``response_data`` attribute when the response
      content-type is JSON.
    * A ``response_json_paths`` response handler is added. Data read
      from disk during this handle will be loaded with the yaml.safe_load
      method to support both JSON and YAML data sources from disk.
    * JSONPaths in $RESPONSE substitutions are supported.
    """

    @staticmethod
    def load_data_file(test, file_path):
        info = test.load_data_file(file_path)
        info = six.text_type(info, 'UTF-8')
        return yaml.safe_load(info)
