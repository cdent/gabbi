#
# Copyright 2014 Red Hat. All Rights Reserved.
#
# Author: Chris Dent <chdent@redhat.com>
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

"""A sample test module to exercise the code.

For the sake of exploratory development.
"""


import json
import os

from six.moves.urllib import parse as urlparse

from gabbi import driver


TESTS_DIR = 'gabbits'
METHODS = ['GET', 'PUT', 'POST', 'DELETE', 'PATCH']


class SimpleWsgi(object):
    """A simple wsgi application to use in tests."""

    def __call__(self, environ, start_response):
        request_method = environ['REQUEST_METHOD'].upper()
        query_data = urlparse.parse_qs(environ.get('QUERY_STRING', ''))

        request_url = environ.get('REQUEST_URI',
                                  environ.get('RAW_URI', 'unknown'))

        path, query, fragment = urlparse.urlsplit(request_url)[2:]
        server_name = environ.get('SERVER_NAME')
        server_port = environ.get('SERVER_PORT')
        server_scheme = environ.get('wsgi.url_scheme')
        if server_port not in ['80', '443']:
            netloc = '%s:%s' % (server_name, server_port)
        else:
            netloc = server_name

        request_url = urlparse.urlunsplit((server_scheme, netloc, path,
                                           query, fragment))

        accept_header = environ.get('HTTP_ACCEPT')

        if accept_header:
            content_type = accept_header
        else:
            content_type = 'application/json'

        headers = [
            ('X-Gabbi-method', request_method),
            ('Content-Type', content_type),
            ('X-Gabbi-url', request_url),
        ]

        if request_method not in METHODS:
            headers.append(
                ('Allow', ', '.join(METHODS)))
            start_response('405 Method Not Allowed', headers)
            return []

        if request_method.startswith('P'):
            body = environ['wsgi.input'].read()
            if body:
                body_data = json.loads(body)
                query_data.update(body_data)
            headers.append(('Location', request_url))

        start_response('200 OK', headers)

        query_output = json.dumps(query_data)
        return [query_output.encode('utf-8')]


def load_tests(loader, tests, pattern):
    """Provide a TestSuite to the discovery process."""
    test_dir = os.path.join(os.path.dirname(__file__), TESTS_DIR)
    return driver.build_tests(test_dir, loader, host=None,
                              intercept=SimpleWsgi)
