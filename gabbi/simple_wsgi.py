#
# Copyright 2014, 2015 Red Hat. All Rights Reserved.
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
"""
SimpleWsgi provides a WSGI callable that can be used in tests to
reflect posted data and otherwise confirm headers and queries.
"""

import json

from six.moves.urllib import parse as urlparse


METHODS = ['GET', 'PUT', 'POST', 'DELETE', 'PATCH']


class SimpleWsgi(object):
    """A simple wsgi application to use in tests."""

    def __call__(self, environ, start_response):
        request_method = environ['REQUEST_METHOD'].upper()
        query_data = urlparse.parse_qs(environ.get('QUERY_STRING', ''))
        request_url = environ.get('REQUEST_URI',
                                  environ.get('RAW_URI', 'unknown'))
        accept_header = environ.get('HTTP_ACCEPT')
        content_type_header = environ.get('CONTENT_TYPE', '')

        request_url = self._fully_qualify(environ, request_url)

        if accept_header:
            response_content_type = accept_header
        else:
            response_content_type = 'application/json'

        headers = [
            ('X-Gabbi-method', request_method),
            ('Content-Type', response_content_type),
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
                if not content_type_header:
                    start_response('400 Bad request', headers)
                    return []
                if content_type_header == 'application/json':
                    body_data = json.loads(body.decode('utf-8'))
                    if query_data:
                        query_data.update(body_data)
                    else:
                        query_data = body_data
            headers.append(('Location', request_url))

        start_response('200 OK', headers)

        query_output = json.dumps(query_data)
        return [query_output.encode('utf-8')]

    @staticmethod
    def _fully_qualify(environ, url):
        """Turn a URL path into a fully qualified URL."""
        path, query, fragment = urlparse.urlsplit(url)[2:]
        server_name = environ.get('SERVER_NAME')
        server_port = environ.get('SERVER_PORT')
        server_scheme = environ.get('wsgi.url_scheme')
        if server_port not in ['80', '443']:
            netloc = '%s:%s' % (server_name, server_port)
        else:
            netloc = server_name

        return urlparse.urlunsplit((server_scheme, netloc, path,
                                    query, fragment))
