# Copyright 2014, 2015 Red Hat
#
# Authors: Chris Dent <chdent@redhat.com>
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
"""Utility functions grab bag."""


def decode_content(response, content):
    """Decode content to a proper string."""
    content_type = response.get('content-type',
                                'application/binary').lower()
    if ';' in content_type:
        content_type, charset = (attr.strip() for attr in
                                 content_type.split(';'))
        charset = charset.split('=')[1].strip()
    else:
        charset = 'utf-8'

    if not_binary(content_type):
        return content.decode(charset)
    else:
        return content


def not_binary(content_type):
    """Decide if something is content we'd like to treat as a string."""
    return (content_type.startswith('text/') or
            content_type.endswith('+xml') or
            content_type.endswith('+json') or
            content_type == 'application/javascript' or
            content_type == 'application/json')
