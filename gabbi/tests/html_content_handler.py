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
"""Create an HTML content handler to test content handlers."""

from lxml import html

from six.moves.urllib import parse as urlparse

from gabbi import handlers


def _parse_selector(selector):
    """
    extracts attribute name from selector, if any

    attributes are appended with `@<name>` (e.g. `a@href`)
    """
    attribute = None
    if "@" in selector:
        selector, attribute = selector.rsplit("@", 1)
    return selector, attribute


class HTMLHandler(handlers.ResponseHandler, handlers.ContentHandler):

    test_key_suffix = 'html'
    test_key_value = {}

    @staticmethod
    def accepts(content_type):
        # TODO(cdent): This is going to be common, should be on the
        # superclass.
        content_type = content_type.split(';', 1)[0].strip()
        if (content_type == 'application/x-www-form-urlencoded'
                or 'html' in content_type):
            return True
        return False

    @staticmethod
    def loads(output):
        return html.fromstring(output)

    def action(self, test, item, value):
        # TODO(FND): There's no template handling in this.
        try: # count
            count = int(value)
        except ValueError: # content
            count = None

        selector, attribute = _parse_selector(item)
        nodes = test.response_data.cssselect(selector)
        node_count = len(nodes)
        if count is not None:
            test.assertEqual(node_count, count,
                    "expected %d elements matching '%s', found %d" % (count,
                            selector, node_count))
            if attribute: # XXX: this is the same as using an attribute selector!?
                for i, node in enumerate(nodes):
                    test.assertTrue(attribute in node.attrib,
                            "missing attribute '%s' on element #%d matching '%s'" %
                                    (attribute, i + 1, selector))
        else:
            test.assertNotEqual(node_count, 0, "no element matching '%s'" % selector)
            test.assertEqual(node_count, 1,
                    "'%s' content check must not target more than a single element" %
                            selector)
            node = nodes[0]
            if attribute:
                actual = node.attrib[attribute]
                test.assertEqual(actual, value,
                        "unexpected value for attribute '%s' on element matching '%s'" %
                                (attribute, selector))
            else:
                actual = node.text.strip()
                test.assertEqual(actual, value, 'Unable to match %s as %s, got %s'
                         % (selector, actual, value))

    @classmethod
    def gen_replacer(cls, test):
        def replace_func(match):
            selector, attribute = _parse_selector(match.group("arg"))

            doc = test.prior.response_data
            nodes = doc.cssselect(selector)
            node_count = len(nodes)
            if node_count == 0:
                raise ValueError("no matching elements for '%s'" % selector)
            elif node_count > 1:
                raise ValueError("more than one matching element for '%s'" % selector)
            node = nodes[0]

            if attribute:
                try:
                    return node.attrib[attribute]
                    # TODO: take `<base>` into account for relative URIs
                except KeyError:
                    raise ValueError("missing attribute '%s' on element matching '%s'" %
                            (attribute, selector))
            else:
                return node.text
        return replace_func

    @staticmethod
    def dumps(data):
        """Turn dict into urlencoded form."""
        # TODO(FND): Because of the escaping that happens here, and
        # the way in which urlencode is overzealous, the $RESPONSE
        # handling can't be done with the output from this. It could 
        # be possible to replicate what is done in gabbi.case to
        # process query strings, but we don't have access to the
        # methods here because we just have data, not the test
        # class.
        return urlparse.urlencode(data, doseq=True)
