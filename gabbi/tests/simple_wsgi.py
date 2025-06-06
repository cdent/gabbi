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
import urllib.parse as urlparse


CURRENT_POLL = 0
METHODS = ['GET', 'PUT', 'POST', 'DELETE', 'PATCH']


class SimpleWsgi:
    """A simple wsgi application to use in tests."""

    def __call__(self, environ, start_response):
        global METHODS
        global CURRENT_POLL

        script_name = environ.get('SCRIPT_NAME', '')
        path_info = environ.get('PATH_INFO', '').removeprefix(script_name)
        request_method = environ['REQUEST_METHOD'].upper()
        query_string = environ.get('QUERY_STRING', '')
        query_data = urlparse.parse_qs(query_string)
        request_url = script_name + path_info
        accept_header = environ.get('HTTP_ACCEPT')
        content_type_header = environ.get('CONTENT_TYPE', '')

        full_request_url = self._fully_qualify(
            environ,
            request_url,
            query_string,
        )

        if accept_header and accept_header != '*/*':
            response_content_type = accept_header
        else:
            # JSON doesn't need a charset but we throw one in here
            # to exercise the decoding code
            response_content_type = (
                'application/json ; charset=utf-8 ; stop=no')

        headers = [
            ('X-Gabbi-method', request_method),
            ('Content-Type', response_content_type),
            ('X-Gabbi-url', full_request_url),
        ]

        if request_method == 'DIE':
            raise Exception('because you asked me to')

        if request_method not in METHODS:
            headers.append(
                ('Allow', ', '.join(METHODS)))
            start_response('405 Method Not Allowed', headers)
            return []

        if request_method.startswith('P'):
            length = int(environ.get('CONTENT_LENGTH', '0'))
            body = environ['wsgi.input'].read(length)
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
            headers.append(('Location', full_request_url))

        if path_info == '/presenter':
            start_response('200 OK', [('Content-Type', 'text/html')])
            return [b"""<!DOCTYPE html>
                    <html>
                        <head>
                            <meta charset="utf-8">
                            <title>Hello World</title>
                        </head>
                        <body>
                            <h1>Hello World</h1>
                            <p>lorem ipsum dolor sit amet</p>
                        </body>
                    </html>
                    """]
        # Provide response that claims to be json but is not.
        elif path_info.startswith('/notjson'):
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [b'not valid json']
        elif path_info.startswith('/poller'):
            if CURRENT_POLL == 0:
                CURRENT_POLL = int(query_data.get('count', [5])[0])
                start_response('400 Bad Reqest', [])
                return []
            else:
                CURRENT_POLL -= 1
                if CURRENT_POLL > 0:
                    start_response('400 Bad Reqest', [])
                    return []
                else:
                    CURRENT_POLL = 0
            # fall through if we've ended the loop
        elif path_info == '/cookie':
            headers.append(('Set-Cookie', 'session=1234; domain=.example.com'))
        elif path_info == '/jsonator':
            json_data = json.dumps({query_data['key'][0]:
                                    query_data['value'][0]})
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [json_data.encode('utf-8')]
        elif path_info == '/nan':
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [json.dumps({
                "nan": float('nan')
            }).encode('utf-8')]
        elif path_info == '/header_key':
            scheme_header = environ.get('HTTP_HTTP', False)

            if scheme_header:
                headers.append(('HTTP', scheme_header))
                start_response('200 OK', headers)
            else:
                start_response('500 SERVER ERROR', headers)

            query_output = json.dumps(query_data)
            return [query_output.encode('utf-8')]
        elif path_info == '/notempty':
            # This block is used to experiment with verbosity handling.
            # See: https://github.com/cdent/gabbi/issues/282
            content_type = query_data.get('content-type', [None])[0]
            headers = []
            if content_type:
                headers.append(('Content-type', content_type))
            start_response('200 OK', headers)
            return ['notempty'.encode('utf-8')]

        start_response('200 OK', headers)

        query_output = json.dumps(query_data)
        return [query_output.encode('utf-8')]

    @staticmethod
    def _fully_qualify(environ, url, query_data):
        """Turn a URL path into a fully qualified URL."""
        split_url = urlparse.urlsplit(url)
        server_name = environ.get('SERVER_NAME')
        server_port = str(environ.get('SERVER_PORT'))
        server_scheme = environ.get('wsgi.url_scheme')
        if server_port not in ['80', '443']:
            netloc = '%s:%s' % (server_name, server_port)
        else:
            netloc = server_name

        return urlparse.urlunsplit((server_scheme, netloc, split_url.path,
                                    query_data, split_url.fragment))
