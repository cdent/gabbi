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

import io
import os

import six
import yaml


try:  # Python 3
    ConnectionRefused = ConnectionRefusedError
except NameError:  # Python 2
    import socket
    ConnectionRefused = socket.error


import colorama
from six.moves.urllib import parse as urlparse


def create_url(base_url, host, port=None, prefix='', ssl=False):
    """Given pieces of a path-based url, return a fully qualified url."""
    scheme = 'http'

    # A host with : in it at this stage is assumed to be an IPv6
    # address of some kind (they come in many forms). Port should
    # already have been stripped off.
    if ':' in host and not (host.startswith('[') and host.endswith(']')):
        host = '[%s]' % host

    if port and not _port_follows_standard(port, ssl):
        netloc = '%s:%s' % (host, port)
    else:
        netloc = host

    if ssl:
        scheme = 'https'

    parsed_url = urlparse.urlsplit(base_url)
    query_string = parsed_url.query
    path = parsed_url.path

    # Guard against a prefix of None
    if prefix:
        path = '%s%s' % (prefix, path)

    return urlparse.urlunsplit((scheme, netloc, path, query_string, ''))


def decode_response_content(header_dict, content):
    """Decode content to a proper string."""
    content_type, charset = extract_content_type(header_dict)

    if not_binary(content_type) and isinstance(content, six.binary_type):
        return content.decode(charset)
    else:
        return content


def extract_content_type(header_dict, default='application/binary'):
    """Extract parsed content-type from headers."""
    content_type = header_dict.get('content-type',
                                   default).strip().lower()
    return parse_content_type(content_type)


def get_colorizer(stream):
    """Return a function to colorize a string.

    Only if stream is a tty .
    """
    if stream.isatty() or os.environ.get('GABBI_FORCE_COLOR', False):
        colorama.init()
        return _colorize
    else:
        return lambda x, y: y


def load_yaml(handle=None, yaml_file=None):
    """Read and parse any YAML file or filehandle.

    Let exceptions flow where they may.

    If no file or handle is provided, read from STDIN.
    """
    if yaml_file:
        with io.open(yaml_file, encoding='utf-8') as source:
            return yaml.safe_load(source.read())

    # This will intentionally raise AttributeError if handle is None.
    return yaml.safe_load(handle.read())


def not_binary(content_type):
    """Decide if something is content we'd like to treat as a string."""
    return (content_type.startswith('text/') or
            content_type.endswith('+xml') or
            content_type.endswith('+json') or
            content_type == 'application/javascript' or
            content_type.startswith('application/json'))


def parse_content_type(content_type, default_charset='utf-8'):
    """Parse content type value for media type and charset."""
    charset = default_charset
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


def host_info_from_target(target, prefix=None):
    """Turn url or host:port and target into test destination."""
    force_ssl = False
    split_url = urlparse.urlparse(target)

    if split_url.scheme:
        if split_url.scheme == 'https':
            force_ssl = True
        return split_url.hostname, split_url.port, split_url.path, force_ssl
    else:
        target = target
        prefix = prefix

    if ':' in target and '[' not in target:
        host, port = target.rsplit(':', 1)
    elif ']:' in target:
        host, port = target.rsplit(':', 1)
    else:
        host = target
        port = None
    host = host.replace('[', '').replace(']', '')

    return host, port, prefix, force_ssl


def _colorize(color, message):
    """Add a color to the message."""
    try:
        return getattr(colorama.Fore, color) + message + colorama.Fore.RESET
    except AttributeError:
        return message


def _port_follows_standard(port, ssl):
    """Return True if a standard port is using a non-standard ssl setting."""
    port = int(port)
    return (port == 443 and ssl) or (port == 80 and not ssl)
