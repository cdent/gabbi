
JSONPath
========

Gabbi makes extensive use of JSONPath to provide a tool for
validating response bodies that are formatted as JSON and making
reference to that JSON in subsequent queries. `jsonpath_rw`_ is used
to process the JSONPath expressions.

To address common requirements when evaluting JSON responses,
extensions have been made to the default implementation of JSONPath
using `jsonpath_rw_ext`. It adds three useful functions:

#. Return the length of the current datum using ``len``.
#. Sort the current datum using ``sorted`` and ``[/name]``.
#. Filter using ``[?name = "cow"]`` to select an item in the
   current datum.

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

There are more JSONPath examples in :doc:`example` and in the
`jsonpath_rw`_ and `jsonpath_rw_ext`_ documentation.

.. _jsonpath_rw: http://jsonpath-rw.readthedocs.org/en/latest/
.. _jsonpath_rw_ext: https://python-jsonpath-rw-ext.readthedocs.org/en/latest/
