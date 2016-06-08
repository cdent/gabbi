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
"""Package for response and content handlers that process the body of
a response in various ways.
"""

from gabbi.handlers import core
from gabbi.handlers import jsonhandler

# A list of the default handlers
RESPONSE_HANDLERS = [
    core.ForbiddenHeadersResponseHandler,
    core.HeadersResponseHandler,
    core.StringResponseHandler,
    jsonhandler.JSONHandler,
]
