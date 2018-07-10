
Content Handlers
================

Content handlers are responsible for preparing request data and
evaluating response data based on the content-type of the request
and response. A content handler operates as follows:

* Structured YAML data provided via the ``data`` attribute is
  converted to a string or bytes sequence and used as request body.
* The response body (a string or sequence of bytes) is transformed
  into a content-type dependent structure and stored in an internal
  attribute named ``response_data`` that is:

  * used when evaluating the response body
  * used in ``$RESPONSE[]`` :ref:`substitutions <state-substitution>`

By default, gabbi provides content handlers for JSON. In that
content handler the ``data`` test key is converted from structured
YAML into a JSON string. Response bodies are converted from a JSON
string into a data structure in ``response_data`` that is used when
evaluating ``response_json_paths`` entries in a test or doing
JSONPath-based ``$RESPONSE[]`` substitutions.

A YAMLDiskLoadingJSONHandler has been added to extend the JSON handler.
It works the same way as the JSON handler except for when evaluating the
``response_json_paths`` handle, data that is read from disk can be either in
JSON or YAML format. The YAMLDiskLoadingJSONHandler is not enabled by default
and must be added as shown in the :ref:`Extensions` section in order to be
used in the tests.

Further content handlers can be added as extensions. Test authors
may need these extensions for their own suites, or enterprising
developers may wish to create and distribute extensions for others
to use.

.. note:: One extension that is likely to be useful is a content handler
          that turns ``data`` into url-encoded form data suitable
          for POST and turns an HTML response into a DOM object.

.. _Extensions:

Extensions
----------

Content handlers are an evolution of the response handler concept in
earlier versions gabbi. To preserve backwards compatibility with
existing response handlers, old style response handlers are still
allowed, but new handlers should implement the content handler
interface (described below).

.. highlight:: python

Registering additional custom handlers is done by passing a subclass
of :class:`~gabbi.handlers.base.ContentHandler` to
:meth:`~gabbi.driver.build_tests`::

    driver.build_tests(test_dir, loader, host=None,
                       intercept=simple_wsgi.SimpleWsgi,
                       content_handlers=[MyContentHandler])

If pytest is being used::

    driver.py_test_generator(test_dir, intercept=simple_wsgi.SimpleWsgi,
                             content_handlers=[MyContenHandler])

Gabbi provides an additional custom handler named YAMLDiskLoadingJSONHandler.
This can be used for loading JSON and YAML files from disk when evaluating the
``response_json_paths`` handle.

.. warning:: YAMLDiskLoadingJSONHandler shares the same content-type as
             the default JSONHandler. When there are multiple handlers
             listed that accept the same content-type, the one that is
             earliest in the list will be used.

With ``gabbi-run``, custom handlers can be loaded via the
``--response-handler`` option -- see
:meth:`~gabbi.runner.load_response_handlers` for details.

.. note:: The use of the ``--response-handler`` argument is done to
          preserve backwards compatibility and avoid excessive arguments.
          Both types of handler may be passed to the argument.

Implementation Details
~~~~~~~~~~~~~~~~~~~~~~

Creating a content handler requires subclassing
:class:`~gabbi.handlers.base.ContentHandler` and implementing several methods.
These methods are described below, but inspecting
:class:`~gabbi.handlers.jsonhandler.JSONHandler` will be instructive in
highlighting required arguments and techniques.

To provide a ``response_<something>`` response-body evaluator a subclass
must define:

* ``test_key_suffix``: This, along with the prefix ``response_``, forms
  the key used in the test structure. It is a class level string.
* ``test_key_value``: The key's default value, either an empty list (``[]``)
  or empty dict (``{}``). It is a class level value.
* ``action``: An instance method which tests the expected values
  against the HTTP response - it is invoked for each entry, with the parameters
  depending on the default value. The arguments to ``action`` are (in order):

  * ``self``: The current instance.
  * ``test``: The currently active ``HTTPTestCase``
  * ``item``: The current entry if ``test_key_value`` is a
    list, otherwise the key half of the key/value pair at this entry.
  * ``value``: ``None`` if ``test_key_value`` is a list, otherwise the
    value half of the key/value pair at this entry.

To translate request or response bodies to or from structured data a
subclass must define an ``accepts`` method. This should return
``True`` if this class is willing to translate the provided
content-type. During request processing it is given the value of the
content-type header that will be sent in the request. During
response processing it is given the value of the content-type header of
the response. This makes it possible to handle different request and
response bodies in the same handler, if desired. For example a
handler might accept ``application/x-www-form-urlencoded`` and
``text/html``.

If ``accepts`` is defined two additional static methods should be defined:

* ``dumps``: Turn structured Python data from the ``data`` key in a test into a
  string or byte stream. The optional ``test`` param allows you to access the
  current test case which may help with manipulations for custom content
  handlers, e.g. ``multipart/form-data`` needs to add a ``boundary`` to the
  ``Content-Type`` header in order to mark the appropriate sections of the
  body.
* ``loads``: Turn a string or byte stream in a response into a Python data
  structure. Gabbi will put this data on the ``response_data``
  attribute on the test, where it can be used in the evaluations
  described above (in the  ``action`` method) or in ``$RESPONSE`` handling.
  An example usage here would be to turn HTML into a DOM.
* ``load_data_file``: Load data from disk into a Python data structure. Gabbi
  will call this method when ``response_<something>`` contains an item where
  the right hand side value starts with ``<@``. The ``test`` param allows you
  to access the current test case and provides a load_data_file method
  which should be used because it verifies the data is loaded within the test
  diectory and returns the file source as a string. The ``load_data_file``
  method was introduced to re-use the JSONHandler in order to support loading
  YAML files from disk through the implementation of an additional custom
  handler, see
  :class:`~gabbi.handlers.yaml_disk_loading_jsonhandler.YAMLDiskLoadingJSONHandler`
  for details.


Finally if a ``replacer`` class method is defined, then when a
``$RESPONSE`` substitution is encountered, ``replacer`` will be
passed the ``response_data`` of the prior test and the argument within the
``$RESPONSE``.

Please see the `JSONHandler source`_ for additional detail.

.. _JSONHandler source: https://github.com/cdent/gabbi/blob/master/gabbi/handlers/jsonhandler.py
