
Content Handlers
================

Gabbi provides an extension system called content handlers that can be
used to expand how different types of request and response content may
be used and evaluated. These make it possible to provide custom code
that does up to four things:

* Translate structured YAML data provided provided to the test
  ``data`` key into a string or sequence of bytes to be used in the
  body of a request.
* Translate the string or sequence of bytes found in the body of a
  response into a ``response_data`` attribute.
* Use the ``response_data`` as source for evaluating the response.
* Use the ``response_data`` in ``$RESPONSE[]`` substitutions.

The JSON support that is built into gabbi is provided by a content
handler that translates ``data`` into a JSON string and translates a
JSON response into a Python data structure that can be evaluated by
JSONPath.

Content handlers are an evolution of the response handler concept in
version 1.x of gabbi. To preserve backwards compatibility with
existing response handlers, old style response handlers are still
allowed, but new handlers should implemented the content handler
interface (described below).

.. highlight:: python

While the default handlers (as described in :doc:`format`) are sufficient for
most cases, it is possible to register additional custom handlers by passing a
subclass of :class:`~gabbi.handlers.ContentHandler` to
:meth:`~gabbi.driver.build_tests`::

    driver.build_tests(test_dir, loader, host=None,
                       intercept=simple_wsgi.SimpleWsgi,
                       content_handlers=[MyContentHandler])

With ``gabbi-run``, custom handlers can be loaded via the
``--response-handler`` option -- see
:meth:`~gabbi.runner.load_response_handlers` for details.

.. note:: The use of the ``--response-handler`` argument is done to
          preserve backwards compatibility. Both types of handler may be
          passed.

Implementation Details
======================

Creating a content handler requires subclassing :class:`~gabbi.handlers.ContentHandler`
and implementing several methods. These methods are described below,
but inspecting :class:`~gabbi.handlers.jsonhandler.JSONHandler`
will be instructive in highlighting required arguments and
techniques.

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
response processing it is given the value of the content-header of
the response. This makes it possible to handle different request and
response bodies in the same handler, if desired. For example a
handler might accept ``application/x-www-form-urlencoded`` and
``text/html``.

If ``accepts`` is defined two additional static methods should be defined::

* ``dumps``: Turn structured Python data from the YAML ``data`` in a
  test into a string or byte stream.
* ``loads``: Turn a string or byte stream in a response into a Python data
  structure. Gabbi will put this data on the ``response_data``
  attribute on the test, where it can be used in the evaluations
  described above or in ``$RESPONSE`` handling. An example usage
  here would be to turn HTML into a DOM.

Finally if a ``replacer`` class method is defined, then when a
``$RESPONSE`` substitution is encountered, ``replacer`` will be
passed the ``response_data`` of the prior test and the argument within the
``$RESPONSE``.

Please see the `JSONHandler source`_ for additional detail.

.. _JSONHandler source: https://github.com/cdent/gabbi/blob/master/gabbi/handlers/jsonhandler.py
