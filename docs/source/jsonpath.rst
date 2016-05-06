JSONPath
========

Gabbi supports JSONPath both for validating JSON response bodies and within
:ref:`substitutions <state-substitution>`.

JSONPath expressions are provided by `jsonpath_rw`_, with
`jsonpath_rw_ext`_ custom extensions to address common requirements:

#. Sorting via ``sorted`` and ``[/property]``.
#. Filtering via ``[?property = value]``.
#. Returning the respective length via ``len``.

(These apply both to arrays and key-value pairs.)

.. highlight:: json

Here is a JSONPath example demonstrating some of these features. Given
JSON data as follows::

    {
        "pets": [
            {"type": "cat", "sound": "meow"},
            {"type": "dog", "sound": "woof"}
        ]
    }

.. highlight:: yaml

If the ordering of the list in ``pets`` is predictable and
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

If it is necessary to validate the entire JSON response use a
JSONPath of ``$``::

    response_json_paths:
        $:
            pets:
                - type: cat
                  sound: meow
                - type: dog
                  sound: woof

This is not a technique that should be used frequently as it can
lead to difficult to read tests and it also indicates that your
gabbi tests are being used to test your serializers and data models,
not just your API interactions.

There are more JSONPath examples in :doc:`example` and in the
`jsonpath_rw`_ and `jsonpath_rw_ext`_ documentation.

.. _jsonpath_rw: http://jsonpath-rw.readthedocs.io/en/latest/
.. _jsonpath_rw_ext: https://python-jsonpath-rw-ext.readthedocs.io/en/latest/
