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
"""Subclass of Http class for verbosity."""

from __future__ import print_function

import os
import sys

import httplib2

from gabbi import utils


class VerboseHttp(httplib2.Http):
    """A subclass of Http that verbosely reports on activity.

    If the output is a tty or ``GABBI_FORCE_COLOR`` is set in the
    environment, then output will be colorized according to ``COLORMAP``.

    Output can include request and response headers, request and
    response body content (if of a printable content-type), or both.

    The color of the output has reasonable defaults. These may be overridden
    by setting the following environment variables

    * GABBI_CAPTION_COLOR
    * GABBI_HEADER_COLOR
    * GABBI_REQUEST_COLOR
    * GABBI_STATUS_COLOR

    to any of: BLACK RED GREEN YELLOW BLUE MAGENTA CYAN WHITE
    """

    # A list of request and response headers to never display.
    # Can include httplib2 response object attributes that are not
    # technically headers.
    HEADER_BLACKLIST = [
        'status',
    ]

    REQUEST_PREFIX = '>'
    RESPONSE_PREFIX = '<'
    COLORMAP = {
        'caption': os.environ.get('GABBI_CAPTION_COLOR', 'BLUE').upper(),
        'header': os.environ.get('GABBI_HEADER_COLOR', 'YELLOW').upper(),
        'request': os.environ.get('GABBI_REQUEST_COLOR', 'CYAN').upper(),
        'status': os.environ.get('GABBI_STATUS_COLOR', 'CYAN').upper(),
    }

    def __init__(self, **kwargs):
        self.caption = kwargs.pop('caption')
        self._show_body = kwargs.pop('body')
        self._show_headers = kwargs.pop('headers')
        self._use_color = kwargs.pop('colorize')
        self._stream = kwargs.pop('stream')
        if self._use_color:
            self.colorize = utils.get_colorizer(self._stream)
        super(VerboseHttp, self).__init__(**kwargs)

    def _request(self, conn, host, absolute_uri, request_uri, method, body,
                 headers, redirections, cachekey):
        """Display request parameters before requesting."""

        self._verbose_output('#### %s ####' % self.caption,
                             color=self.COLORMAP['caption'])
        self._verbose_output('%s %s' % (method, request_uri),
                             prefix=self.REQUEST_PREFIX,
                             color=self.COLORMAP['request'])
        self._print_header("Host", host, prefix=self.REQUEST_PREFIX)

        self._print_headers(headers, prefix=self.REQUEST_PREFIX)
        self._print_body(headers, body)

        (response, content) = httplib2.Http._request(
            self, conn, host, absolute_uri, request_uri, method, body,
            headers, redirections, cachekey
        )

        # Blank line for division
        self._verbose_output('')
        self._verbose_output('%s %s' % (response['status'], response.reason),
                             prefix=self.RESPONSE_PREFIX,
                             color=self.COLORMAP['status'])
        self._print_headers(response, prefix=self.RESPONSE_PREFIX)

        # response body
        self._print_body(response, content)
        self._verbose_output('')

        return (response, content)

    def _print_headers(self, headers, prefix=''):
        if self._show_headers:
            for key in headers:
                if key not in self.HEADER_BLACKLIST:
                    self._print_header(key, headers[key], prefix=prefix)

    def _print_body(self, headers, content):
        if self._show_body and utils.not_binary(
                utils.extract_content_type(headers)[0]):
            self._verbose_output('')
            self._verbose_output(
                utils.decode_response_content(headers, content))

    def _print_header(self, name, value, prefix='', stream=None):
        header = self.colorize(self.COLORMAP['header'], "%s:" % name)
        self._verbose_output("%s %s" % (header, value), prefix=prefix,
                             stream=stream)

    def _verbose_output(self, message, prefix='', color=None, stream=None):
        """Output a message."""
        stream = stream or self._stream
        if prefix and message:
            print(prefix, end=' ', file=stream)
        if color:
            message = self.colorize(color, message)
        print(message, file=stream)


def get_http(verbose=False, caption=''):
    """Return an Http class for making requests."""
    if verbose:
        body = True
        headers = True
        colorize = True
        stream = sys.stdout
        if verbose == 'body':
            headers = False
        if verbose == 'headers':
            body = False
        return VerboseHttp(body=body, headers=headers, colorize=colorize,
                           stream=stream, caption=caption)
    return httplib2.Http()
