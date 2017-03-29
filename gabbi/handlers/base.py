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
"""Base classes for response and content handlers."""


from gabbi.exception import GabbiFormatError


class ResponseHandler(object):
    """Add functionality for making assertions about an HTTP response.

    A subclass may implement two methods: ``action`` and ``preprocess``.

    ``preprocess`` takes one argument, the ``TestCase``. It is called exactly
    once for each test before looping across the assertions. It is used,
    rarely, to copy the ``test.output`` into a useful form (such as a parsed
    DOM).

    ``action`` takes two or three arguments. If ``test_key_value`` is a list
    ``action`` is called with the test case and a single list item. If
    ``test_key_value`` is a dict then ``action`` is called with the test case
    and a key and value pair.
    """

    test_key_suffix = ''
    test_key_value = []

    def __init__(self):
        self._register()

    def __call__(self, test):
        if test.test_data[self._key]:
            self.preprocess(test)
            if type(self.test_key_value) != type(test.test_data[self._key]):
                raise GabbiFormatError(
                    "%s in '%s' has incorrect type, must be %s"
                    % (self._key, test.test_data['name'],
                       type(self.test_key_value)))
            for item in test.test_data[self._key]:
                try:
                    value = test.test_data[self._key][item]
                except (TypeError, KeyError):
                    value = None
                self.action(test, item, value=value)

    def preprocess(self, test):
        """Do any pre-single-test preprocessing."""
        pass

    def action(self, test, item, value=None):
        """Test an individual entry for this response handler.

        If the entry is a key value pair the key is in item and the
        value in value. Otherwise the entry is considered a single item
        from a list.
        """
        pass

    def _register(self):
        """Register this handler on the provided test class."""
        self.response_handler = None
        self.content_handler = None
        if self.test_key_suffix:
            self._key = 'response_%s' % self.test_key_suffix
            self.test_base = {self._key: self.test_key_value}
            self.response_handler = self
        if hasattr(self, 'accepts'):
            self.content_handler = self

    def __eq__(self, other):
        if isinstance(other, ResponseHandler):
            return self.__class__ == other.__class__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class ContentHandler(ResponseHandler):
    """A subclass of ResponseHandlers that adds content handling."""

    @staticmethod
    def accepts(content_type):
        """Return True if this handler can handler this type."""
        return False

    @classmethod
    def replacer(cls, response_data, path):
        """Return the string that is replacing RESPONSE."""
        return path

    @staticmethod
    def dumps(data, pretty=False, test=None):
        """Return structured data as a string.

        If pretty is true, prettify.
        """
        return data

    @staticmethod
    def loads(data):
        """Create structured (Python) data from a stream."""
        return data
