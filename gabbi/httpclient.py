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

from __future__ import print_function

import os
import sys

import certifi
import six
import urllib3

from gabbi.handlers import jsonhandler
from gabbi import utils

# Disable SSL warnings otherwise tests which process stderr will get
# extra information.
urllib3.disable_warnings()


class Http(urllib3.PoolManager):
    """A subclass of the ``urllib3.PoolManager`` to munge the data.

    This transforms the response to look more like what httplib2
    provided when it was used as the HTTP client.
    """

    def request(self, absolute_uri, method, body, headers, redirect):
        if redirect:
            retry = urllib3.util.Retry(raise_on_redirect=False, redirect=5)
        else:
            retry = urllib3.util.Retry(total=False, redirect=False)
        response = super(Http, self).request(
            method, absolute_uri, body=body, headers=headers, retries=retry)

        # Transform response into something akin to httplib2
        # response object.
        content = response.data
        status = response.status
        reason = response.reason
        headers = response.headers
        headers['status'] = str(status)
        headers['reason'] = reason
        return headers, content


class VerboseHttp(Http):
    """A subclass of ``Http`` that verbosely reports on activity.

    If the output is a tty or ``GABBI_FORCE_COLOR`` is set in the
    environment, then output will be colorized according to ``COLORMAP``.

    Output can include request and response headers, request and
    response body content (if of a printable content type), or both.

    The color of the output has reasonable defaults. These may be overridden
    by setting the following environment variables

    * ``GABBI_CAPTION_COLOR``
    * ``GABBI_HEADER_COLOR``
    * ``GABBI_REQUEST_COLOR``
    * ``GABBI_STATUS_COLOR``

    to any of: BLACK RED GREEN YELLOW BLUE MAGENTA CYAN WHITE
    """

    # A list of request and response headers to never display.
    # Can include response object attributes that are not
    # technically headers.
    HEADER_BLACKLIST = [
        'status',
        'reason',
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

    def request(self, absolute_uri, method, body, headers, redirect):
        """Display request parameters before requesting."""

        self._verbose_output('#### %s ####' % self.caption,
                             color=self.COLORMAP['caption'])
        self._verbose_output('%s %s' % (method, absolute_uri),
                             prefix=self.REQUEST_PREFIX,
                             color=self.COLORMAP['request'])

        self._print_headers(headers, prefix=self.REQUEST_PREFIX)
        self._print_body(headers, body)

        response, content = super(VerboseHttp, self).request(
            absolute_uri, method, body, headers, redirect)

        # Blank line for division
        self._verbose_output('')
        self._verbose_output('%s %s' % (response['status'],
                                        response['reason']),
                             prefix=self.RESPONSE_PREFIX,
                             color=self.COLORMAP['status'])
        self._print_headers(response, prefix=self.RESPONSE_PREFIX)

        # response body
        self._print_body(response, content)
        self._verbose_output('')

        return (response, content)

    def _print_headers(self, headers, prefix=''):
        """Output request or response headers."""
        if self._show_headers:
            for key in headers:
                if key not in self.HEADER_BLACKLIST:
                    self._print_header(key, headers[key], prefix=prefix)

    def _print_body(self, headers, content):
        """Output body if not binary."""
        # Use text/plain as the default so that when there is not content-type
        # we can still see the output.
        content_type = utils.extract_content_type(headers, 'text/plain')[0]
        if self._show_body and utils.not_binary(content_type):
            content = utils.decode_response_content(headers, content)
            if isinstance(content, six.binary_type):
                content = content.decode('utf-8')
            # TODO(cdent): Using the JSONHandler here instead of
            # just the json module to make it clear that eventually
            # we could pretty print any printable output by using a
            # handler's loads() and dumps(). Not doing that now
            # because it would be pointless (no other interesting
            # handlers) and this approach may be entirely wrong.
            if content and jsonhandler.JSONHandler.accepts(content_type):
                try:
                    data = jsonhandler.JSONHandler.loads(content)
                    content = jsonhandler.JSONHandler.dumps(data, pretty=True)
                except ValueError:
                    # It it didn't decode for some reason treat it as a string.
                    pass
            self._verbose_output('')
            if content:
                self._verbose_output(content)

    def _print_header(self, name, value, prefix='', stream=None):
        """Output one single header."""
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


def get_http(verbose=False, caption='', cert_validate=True):
    """Return an ``Http`` class for making requests."""
    cert_validation = {'cert_reqs': 'CERT_NONE'} if not cert_validate else {}

    if not verbose:
        return Http(strict=True, ca_certs=certifi.where(), **cert_validation)

    headers = False if verbose == 'body' else True
    body = False if verbose == 'headers' else True
    return VerboseHttp(headers=headers, body=body, stream=sys.stdout,
                       caption=caption, colorize=True, strict=True,
                       ca_certs=certifi.where(), **cert_validation)
