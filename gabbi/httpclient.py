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

import sys

import httplib2

from gabbi import utils


class VerboseHttp(httplib2.Http):
    """A subclass of Http that verbosely reports on activity."""

    # A list of headers to never display
    HEADER_BLACKLIST = [
        'status',
    ]

    REQUEST_PREFIX = '>'
    RESPONSE_PREFIX = '<'

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

        self._verbose_output('#### %s ####' % self.caption, color='BLUE')
        self._verbose_output('%s %s' % (method, request_uri),
                             prefix=self.REQUEST_PREFIX)
        self._verbose_output('Host: %s' % host,
                             prefix=self.REQUEST_PREFIX)

        self._do_show_headers(headers, prefix=self.REQUEST_PREFIX)
        self._do_show_body(headers, body)

        (response, content) = httplib2.Http._request(
            self, conn, host, absolute_uri, request_uri, method, body,
            headers, redirections, cachekey
        )

        # Blank line for division
        self._verbose_output('')
        self._verbose_output('%s %s' % (response['status'], response.reason),
                             prefix=self.RESPONSE_PREFIX)
        self._do_show_headers(response, prefix=self.RESPONSE_PREFIX)

        # response body
        self._do_show_body(response, content)
        self._verbose_output('')

        return (response, content)

    def _do_show_headers(self, headers, prefix=''):
        if self._show_headers:
            for key in headers:
                if key not in self.HEADER_BLACKLIST:
                    self._verbose_output('%s: %s' % (key, headers[key]),
                                         prefix=prefix)

    def _do_show_body(self, headers, content):
        if self._show_body and utils.not_binary(
                utils.extract_content_type(headers)[0]):
            self._verbose_output('')
            self._verbose_output(
                utils.decode_response_content(headers, content))

    def _verbose_output(self, message, prefix='', color=None, stream=None):
        """Output a message."""
        stream = stream or self._stream
        if prefix and message:
            print(prefix, end=' ', file=self._stream)
        if color:
            message = self.colorize(color, message)
        print(message, file=self._stream)


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
