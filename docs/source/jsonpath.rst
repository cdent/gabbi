.. _jsonpath:

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

It is also possible to read raw JSON from disk for either all or
some of a JSON response::

    response_json_paths:
        $: @<data.json

or::

    response_json_paths:
        $.pets: <@pets.json
        $.pets[0]: <@cat.json

Examples like this can be found in one of gabbi's `own tests`_.

If it is desired to load YAML files like the JSON ones above, two things must
be done:

#. The YAMLDiskLoadingJSONHandler custom content handler must be passed to the
   driver through the content_handlers argument. See :ref:`Extensions` on how
   to do this.
#. The YAML files to load must be placed in a subdirectory to prevent the test
   runner from consuming them as test files to run::

    response_json_paths:
        $: @<subdir/values.yaml

When reading from disk you can apply the same JSONPath by adding a ':' to the
end of your file name. This allows you to store multiple API responses into
a single file to reduce file management when constructing your tests.

.. highlight:: json

Given JSON data as follows::

    {
        "values": [{
            "pets": [{
                "type": "cat",
                "sound": "meow"
            }, {
                "type": "dog",
                "sound": "woof"
            }]
        }, {
            "people": [{
                "name": "chris",
                "id": 1
            }, {
                "name": "justin",
                "id": 2
            }]
        }]
    }

.. highlight:: yaml

You can write your tests like the following::

    response_json_paths:
        $.pets: <@pets.json
        $.pets[?type = "cat"].sound: <@values.json:$.values[0].pets[?type = "cat"].sound

Although placing more than one API response into a single JSON file may seem
convenient, keep in mind there is a tradeoff in readability that should not
be overlooked before implementing this technique.

Examples like this can be found in one of gabbi's `yaml-from-disk tests`_.

There are more JSONPath examples in :doc:`example` and in the
`jsonpath_rw`_ and `jsonpath_rw_ext`_ documentation.

.. _json-subs:

Substitution
------------

:ref:`Substitutions <state-substitution>` can be made in both the
left (query) and right (expected) hand sides of the json path
expression. When subtitutions are used in the query, care must be
taken to ensure proper quoting of the resulting value. For example
if there is a uuid (with hyphens) at ``$RESPONSE['$.id']`` then this
expression may fail::

    $.nested.structure.$RESPONSE['$.id'].name: foobar

as it will evaluate to something like::

   $.nested.structure.ADC8AAFC-D564-40D1-9724-7680D3C010C2.name: foobar

which may be treated as an arithemtic expression by the json path
parser. The test author should write::

    $.nested.structure["$RESPONSE['$.id']"].name: foobar

to quote the result of the substitution.

.. _jsonpath_rw: http://jsonpath-rw.readthedocs.io/en/latest/
.. _jsonpath_rw_ext: https://python-jsonpath-rw-ext.readthedocs.io/en/latest/
.. _own tests: https://github.com/cdent/gabbi/blob/master/gabbi/tests/gabbits_intercept/data.yaml
.. _yaml-from-disk tests: https://github.com/cdent/gabbi/blob/master/gabbi/tests/gabbits_handlers/yaml-from-disk.yaml
