
JSONPath
========

Gabbi makes extensive use of JSONPath to provide a tool for
validating response bodies that are formatted as JSON and making
reference to that JSON in subsequent queries. `jsonpath_rw`_ is used
to process the JSONPath expressions.

To address a common requirement when evaluting JSON responses, an
extension has been made to the default implementation of JSONPath.
This extension is ``len`` and will return the length of the current
datum in the JSONPath expression.

Here is a simple JSONPath example, including use of ``len``. Given JSON data
as follows::

    {
        "alpha": ["one", "two"],
        "beta": "hello"
    }

it is possible to get information about the values and length as
follows::

    response_json_paths:
        # the dict has two keys
        $.`len`: 2
        # The elements of the alpha list
        $.alpha[0]: one
        $.alpha.[1]: two
        # the alpha list has two items
        $.alpha.`len`: 2
        # The string at beta is hello
        $.beta: hello
        # The string at beta has five chars
        $.beta.`len`: 5

There are more JSONPath examples in :doc:`example`.

.. _jsonpath_rw: http://jsonpath-rw.readthedocs.org/en/latest/
