Test Format
===========

Gabbi tests are expressed in YAML containing an HTTP request and an
expected response. Each YAML file is an ordered sequence of requests.
The bare minimum YAML file for a single request is::

    tests:
       - name: the name of a test
         url: /

This will make a request to ``/`` on whatever the configured
:doc:`host` is. The test will pass if the status of the HTTP response
is ``200``.

The ``tests`` sequence can contain as many requests as required.
Other top level keys are:

* ``fixtures``: A sequence of named :doc:`fixtures`.
* ``defaults``: A dictionary of local default values for the requests and
  responses in the ``tests`` in this file. These override the global
  defaults (explained below).

Each test can use the following structure. Only ``name`` and ``url``
are required. For examples see `the gabbi tests`_. Most of
these allow substitutions (explained below).

* ``name``: The name of the test. Should be unique in this file. When
  tests are dynamically generated the ``TestCase`` name will include
  this name, lowercased with spaces transformed to ``_``. In at least
  some test runners this will allow you to select and filter on test
  name. **Required**
* ``desc``: An arbitrary string describing this test. This is perhaps
  redundant as YAML allows comments. However it's here in case other
  tooling might use it.
* ``url``: The URL to request. This can either be a full path or a
  fully qualified URL (with host and scheme). If not qualified the
  test builder will be responsible for determining host and scheme.
  **Required**
* ``method``: The request method to use. Defaults to ``GET``.
* ``status``: The expected response status code. The default is
  ``200``. If necessary you may indicate multiple response codes
  separated by ``||`` (e.g. ``302 || 301``). Avoid this if possible as
  it indicates there is ambiguity in your tests or your API. Ambiguity
  is bad.
* ``ssl``: Make this request use SSL? Defaults to ``False``. This only
  comes into play if the ``url`` does not provide a scheme (see
  :doc:`host` for more info).
* ``verbose``: If ``True`` print a representation of the current
  request and response to ``stdout``. Defaults to ``False``.
* ``redirects``: If ``True`` automatically follow redirects. Defaults
  to ``False``.
* ``request_headers``: A dictionary of key-value pairs representing
  request header names and values. These will be added to the
  constructed request.
* ``data``: A representation to pass as the body of a request. If you
  use this you should set ``content-type`` in ``request_headers`` to
  something meaningful. See `Data`_ below for more details.
* ``skip``: A string message which if set will cause the test to be
  skipped with the provided message.
* ``xfail``: If ``True`` expect this test to fail but run it anyway.
* ``response_headers``: A dictionary of key-value pairs representing
  expected response headers. If the value of a header is wrapped in
  ``/``, it will be treated as a raw regular expression string.
* ``response_strings``: A sequence of string fragments expected to be
  in the response body.
* ``response_json_paths``: A dictionary of JSONPath rules paired with
  expected matches.
* ``poll``: A dictionary of two keys:

  * ``count``: An integer stating the number of times to attempt
    this test before giving up.
  * ``delay``: A floating point number of seconds to delay between
    attemmpts.

  This makes it possible to poll for a resource created via an
  asynchronous request. Use with caution.

The ``response_*`` items are examples of Response Handlers. Additional
handlers may be created by test authors for specific use cases. See
:doc:`handlers` for more information.

There are a number of magical variables that can be used to make
reference to the state of a current test or the one just prior. These
are replaced with real values during test processing. They are
processed in the order given.

* ``$SCHEME``: The current scheme/protocol (usually ``http`` or ``https``).
* ``$NETLOC``: The host and potentially port of the request.
* ``$ENVIRON['<environment variable>']``: The name of an environment
  variable. Its value will replace the magical variable. If the
  string value of the environment variable is ``"True"`` or
  ``"False"`` then the resulting value will be the corresponding
  boolean, not a string.
* ``$LOCATION``: The location header returned in the prior response.
* ``$HEADERS['<header>']``: Indicate the name of a header from the
  prior response to inject in the value.
* ``$RESPONSE['<json path>']``: A JSONPath query into the prior
  response. See http://jsonpath-rw.readthedocs.org/en/latest/ for
  jsonpath-rw formatting.

All of these variables may be used in all of the following fields:

* ``url``
* ``data``
* ``request_headers``
* ``response_strings``
* ``response_json_paths`` (on the value side of the key value pair)
* ``response_headers`` (on the value side of the key value pair)

With these variables it ought to be possible to traverse an API without any
explicit statements about the URLs being used. If you need a
replacement on a field that is not currently supported please raise
an issue or provide a patch.

As all of these features needed to be tested in the development of
gabbi itself, `the gabbi tests`_ are a good source of examples on how
to use the functionality. See also :doc:`example` for a collection
of examples.

Data
----

The ``data`` key has some special handing to allow for a bit more
flexibility when doing a ``POST`` or ``PUT``. If the value is not a
string (that is, it is a sequence or structure) it is treated as a
data structure which is turned into a JSON string. If the value is a
string that begins with ``<@`` then the rest of the string is treated
as the name of a file to be loaded from the same directory as the YAML
file. If the value is an undecorated string, that's the value.

When reading from a file care should be taken to ensure that a
reasonable content-type is set for the data as this will control if any
encoding is done of the resulting string value. If it is text, json, xml
or javascript it will be encoded to UTF-8.

.. _the gabbi tests: https://github.com/cdent/gabbi/tree/master/gabbi/gabbits_intercept
