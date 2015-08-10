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

import os

import colorama


try:  # Python 3
    ConnectionRefused = ConnectionRefusedError
except NameError:  # Python 2
    import socket
    ConnectionRefused = socket.error


def decode_response_content(header_dict, content):
    """Decode content to a proper string."""
    content_type, charset = extract_content_type(header_dict)

    if not_binary(content_type):
        return content.decode(charset)
    else:
        return content


def extract_content_type(header_dict):
    """Extract content-type from headers."""
    content_type = header_dict.get('content-type',
                                   'application/binary').strip().lower()
    charset = 'utf-8'
    if ';' in content_type:
        content_type, parameter_strings = (attr.strip() for attr
                                           in content_type.split(';', 1))
        try:
            parameter_pairs = [atom.strip().split('=')
                               for atom in parameter_strings.split(';')]
            parameters = {name: value for name, value in parameter_pairs}
            charset = parameters['charset']
        except (ValueError, KeyError):
            # KeyError when no charset found.
            # ValueError when the parameter_strings are poorly
            # formed (for example trailing ;)
            pass

    return (content_type, charset)


def get_colorizer(stream):
    """Return a function to colorize a string.

    Only if stream is a tty .
    """
    if stream.isatty() or os.environ.get('GABBI_FORCE_COLOR', False):
        colorama.init()
        return _colorize
    else:
        return lambda x, y: y


def not_binary(content_type):
    """Decide if something is content we'd like to treat as a string."""
    return (content_type.startswith('text/') or
            content_type.endswith('+xml') or
            content_type.endswith('+json') or
            content_type == 'application/javascript' or
            content_type.startswith('application/json'))


def _colorize(color, message):
    """Add a color to the message."""
    try:
        return getattr(colorama.Fore, color) + message + colorama.Fore.RESET
    except AttributeError:
        return message
