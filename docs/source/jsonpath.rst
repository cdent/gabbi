
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

.. highlight:: json

Here is a JSONPath example demonstrating some of these features. Given
JSON data as follows::

    {"pets": [
        {"type": "cat", "sound": "meow"},
        {"type": "dog", "sound": "woof"}
    ]}

.. highlight:: yaml

if the ordering of the list in ``pets`` is predictable and
reliable it is relatively straightforward to test values::

    response_json_paths:
        # length of list is two
        $.pets.`len`: 2
        # sound of second item in list is woof
        $.pets[1].sound: woof

If the ordering is *not* predictable additional effort is required::

    response_json_paths:
        # sort by type
        $.pets[/type][0].sound: meow
        # sort by type, reversed
        $.pets[\type][0].sound: woof
        # all the sounds
        $.pets[/type]..sound: ['meow', 'woof']
        # filter by type = dog
        $.pets[?type = "dog"].sound: woof

There are more JSONPath examples in :doc:`example` and in the
`jsonpath_rw`_ and `jsonpath_rw_ext`_ documentation.

.. _jsonpath_rw: http://jsonpath-rw.readthedocs.org/en/latest/
.. _jsonpath_rw_ext: https://python-jsonpath-rw-ext.readthedocs.org/en/latest/
