.. highlight:: yaml


Test Format
===========

Gabbi tests are expressed in YAML as a series of HTTP requests with their
expected response::

    tests:
       - name: retrieve root
         GET: /
         status: 200

This will trigger a ``GET`` request to ``/`` on the configured :doc:`host`. The
test will pass if the response's status code is ``200``.


.. _test-structure:

Test Structure
--------------

The top-level ``tests`` category contains an ordered sequence of test
declarations, each describing the expected response to a given request:

.. _metadata:

Metadata
********

.. list-table::
   :header-rows: 1

   * - Key
     - Description
     - Notes
   * - ``name``
     - The test's name. Must be unique within a file.
     - **required**
   * - ``desc``
     - An arbitrary string describing the test.
     -
   * - ``verbose``
     - If ``True`` or ``all`` (synonymous), prints a representation of the
       current request and response to ``stdout``, including both headers and
       body. If set to ``headers`` or ``body``, only the corresponding part of
       the request and response will be printed. If the output is a TTY, colors
       will be used. If the body content-type is JSON it will be formatted for
       improved readability. See :class:`~gabbi.httpclient.VerboseHttp` for
       details.
     - defaults to ``False``
   * - ``skip``
     - A string message which if set will cause the test to be skipped with the
       provided message.
     - defaults to ``False``
   * - ``xfail``
     - Determines whether to expect this test to fail. Note that the test will
       be run anyway.
     - defaults to ``False``
   * - ``use_prior_test``
     - Determines if this test will be run in sequence (after) the test prior
       to it in the list of tests within a file. To be concrete, when this is
       ``True`` the test is dependent on the prior test and if that prior
       has not yet run, it wil be run, even if only the current test has been
       selected. Set this to ``False`` to allow selecting a test without
       dependencies.
     - defaults to ``True``
   * - ``cert_validate``
     - States whether the underlying HTTP client should attempt to validate SSL
       certificates. In many test environment certificates will be self-signed
       so changing this may be requried. It can also be changed when
       :doc:`loader` or using :doc:`gabbi-run <runner>`.
     - defaults to ``True``


.. note:: When tests are generated dynamically, the ``TestCase`` name will
          include the respective test's ``name``, lowercased with spaces
          transformed to ``_``. In at least some test runners this will allow
          you to select and filter on test name.

.. _request-parameters:

Request Parameters
******************

.. table::

   ====================  ========================================  ============
   Key                   Description                               Notes
   ====================  ========================================  ============
   any uppercase string  Any such key is considered an HTTP
                         method, with the corresponding value
                         expressing the URL.

                         This is a shortcut combining ``method``
                         and ``url`` into a single statement::

                             GET: /index

                         corresponds to::

                             method: GET
                             url: /index

   ``method``            The HTTP request method.                  defaults to
                                                                   ``GET``

   ``url``               The URL to request. This can either be a  Either this
                         full path (e.g. "/index") or a fully      or the
                         qualified URL (i.e. including host and    shortcut
                         scheme, e.g.                              above is
                         "http://example.org/index") — see         **required**
                         :doc:`host` for details.

   ``request_headers``   A dictionary of key-value pairs
                         representing request header names and
                         values. These will be added to the
                         constructed request.

   ``query_parameters``  A dictionary of query parameters that
                         will be added to the ``url`` as query
                         string. If that URL already contains a
                         set of query parameters, those wil be
                         extended. See :doc:`example` for a
                         demonstration of how the data is
                         structured.

   ``data``              A representation to pass as the body of
                         a request. Note that ``content-type`` in
                         ``request_headers`` should also be set —
                         see `Data`_ for details.

   ``redirects``         If ``True``, redirects will               defaults to
                         automatically be followed.                ``False``

   ``ssl``               Determines whether the request uses SSL   defaults to
                         (i.e. HTTPS). Note that the ``url``'s     ``False``
                         scheme takes precedence if present — see
                         :doc:`host` for details.
   ====================  ========================================  ============

.. _response-expectations:

Response Expectations
*********************

.. table::

   ==============================  =====================================  ============
   Key                             Description                            Notes
   ==============================  =====================================  ============
   ``status``                      The expected response status code.     defaults to
                                   Multiple acceptable response codes     ``200``
                                   may be provided, separated by ``||``
                                   (e.g. ``302 || 301`` — note, however,
                                   that this indicates ambiguity, which
                                   is generally undesirable).

   ``response_headers``            A dictionary of key-value pairs
                                   representing expected response header
                                   names and values. If a header's value
                                   is wrapped in ``/.../``, it will be
                                   treated as a regular expression to
                                   search for in the response header.

   ``response_forbidden_headers``  A list of headers which must `not`
                                   be present.

   ``response_strings``            A list of string fragments expected
                                   to be present in the response body.

   ``response_json_paths``         A dictionary of JSONPath rules paired
                                   with expected matches. Using this
                                   rule requires that the content being
                                   sent from the server is JSON (i.e. a
                                   content type of ``application/json``
                                   or containing ``+json``)

                                   If the value is wrapped in ``/.../``
                                   the result of the JSONPath query
                                   will be searched for the
                                   value as a regular expression.

   ``poll``                        A dictionary of two keys:

                                   * ``count``: An integer stating the
                                     number of times to attempt this
                                     test before giving up.
                                   * ``delay``: A floating point number
                                     of seconds to delay between
                                     attempts.

                                   This makes it possible to poll for a
                                   resource created via an asynchronous
                                   request. Use with caution.
   ==============================  =====================================  ============

Note that many of these items allow :ref:`substitutions <state-substitution>`.

Default values for a file's ``tests`` may be provided via the top-level
``defaults`` category. These take precedence over the global defaults
(explained below).

For examples see `the gabbi tests`_, :doc:`example` and the `gabbi-demo`_
tutorial.


.. _fixtures:

Fixtures
--------

The top-level ``fixtures`` category contains a sequence of named
:doc:`fixtures`.


.. _response-handlers:

Response Handlers
-----------------

``response_*`` keys are examples of Response Handlers. Custom handlers may be
created by test authors for specific use cases. See :doc:`handlers` for more
information.


.. _state-substitution:

Substitution
------------

There are a number of magical variables that can be used to make
reference to the state of a current test, the one just prior or any
test prior to the current one. The variables are replaced with real
values during test processing.

Global
******

* ``$ENVIRON['<environment variable>']``: The name of an environment
  variable. Its value will replace the magical variable. If the
  string value of the environment variable is ``"True"`` or
  ``"False"`` then the resulting value will be the corresponding
  boolean, not a string.

Current Test
************

* ``$SCHEME``: The current scheme/protocol (usually ``http`` or ``https``).
* ``$NETLOC``: The host and potentially port of the request.

Immediately Prior Test
**********************

* ``$COOKIE``: All the cookies set by any ``Set-Cookie`` headers in
  the prior response, including only the cookie key and value pairs
  and no metadata (e.g. ``expires`` or ``domain``).
* ``$URL``: The URL defined in the prior request, after
  substitutions have been made. For backwards compatibility with
  earlier releases ``$LAST_URL`` may also be used, but if
  ``$HISTORY`` (see below) is being used, ``$URL`` must be used.
* ``$LOCATION``: The location header returned in the prior response.
* ``$HEADERS['<header>']``: The value of any header from the
  prior response.
* ``$RESPONSE['<json path>']``: A JSONPath query into the prior
  response. See :doc:`jsonpath` for more on formatting.

Any Previous Test
*****************

* ``$HISTORY['<test name>'].<magical variable expression>``: Any variable
  which refers to a prior test may be used in an expression that refers to
  any earlier test in the same file by identifying the target test by its
  name in a ``$HISTORY`` dictionary. For example, to refer to a value
  in a JSON object in the response of a test named ``post json``::

    $HISTORY['post json'].$RESPONSE['$.key']

  This is a very powerful feature that could lead to test that are
  difficult for humans to read. Take care to optimize for the
  maintainers that will come after you, not yourself.

.. note:: Where a single-quote character, ``'``, is shown in the variables
          above you may also use a double-quote character, ``"``, but in any
          given expression the same character must be used at both ends.

All of these variables may be used in all of the following fields:

* ``url``
* ``query_parameters``
* ``data``
* ``request_headers`` (in both the key and value)
* ``response_strings``
* ``response_json_paths`` (in both the key and value, see
  :ref:`json path substitution <json-subs>` for more info)
* ``response_headers`` (in both the key and value)
* ``response_forbidden_headers``
* ``count`` and ``delay`` fields of ``poll``

With these variables it ought to be possible to traverse an API without any
explicit statements about the URLs being used. If you need a
replacement on a field that is not currently supported please raise
an issue or provide a patch.

As all of these features needed to be tested in the development of
gabbi itself, `the gabbi tests`_ are a good source of examples on how
to use the functionality. See also :doc:`example` for a collection
of examples and the `gabbi-demo`_ tutorial.


.. _data:

Data
----

The ``data`` key has some special handing to allow for a bit more
flexibility when doing a ``POST`` or ``PUT``:

* If the value is not a string (that is, it is a sequence or structure)
  it is treated as a data structure that will be turned into a
  string by the ``dumps`` method on the relevant
  :doc:`content handler <handlers>`. For example if the content-type of
  the body is ``application/json`` the data structure will be turned
  into a JSON string.
* If the value is a string that begins with ``<@`` then the rest of the
  string is treated as a filepath to be loaded. The path is relative
  to the test directory and may not traverse up into parent directories.
* If the value is an undecorated string, that's the value.

.. note:: When reading from a file care should be taken to ensure that a
          reasonable content-type is set for the data as this will control
          if any encoding is done of the resulting string value. If it
          is text, json, xml or javascript it will be encoded to UTF-8.


.. _the gabbi tests: https://github.com/cdent/gabbi/tree/main/gabbi/tests/gabbits_intercept
.. _gabbi-demo: https://github.com/cdent/gabbi-demo
