Release Notes
=============

These are informal release notes for gabbi since version 1.0.0,
highlighting major features and changes. For more detail see
the `commit logs`_ on GitHub.

2.0.4
-----

* If no content-type is provided with a response and verbose is on for
  responses, display the response body as if it were text.

2.0.3
-----

* Properly declare that gabbi 2.x is Python 3 only.

2.0.1
-----

* Correct management of response handler default fields.

2.0.0
-----

* Drop support for Python 2. If you need Python 2 support, use an older version.
* Stop using ``testtools`` and ``fixtures``. These two modules present several
  difficulties and their maintenance situation suggests those difficulties
  will not be resolved. Since Python 2 support is being removed, the need for
  the modules can be removed as well without losing functionality. "Inner
  fixtures" that use the ``fixtures.Fixture`` interface should continue to
  work.

1.49.0
------

* Add support for not validating certificates in ``https`` requests. Controlled
  by the ``cert_validate`` attribute in individual tests and
  :meth:`~gabbi.driver.build_tests` and the ``-k`` or ``--insecure`` argument to
  :doc:`gabbi-run <runner>`.

1.48.0
------

* Support ``pytest 5.0.0`` in Python ``>=3.5``. For earlier versions of Python,
  ``pytest<5.0.0`` will be used; the pytest project is dropping support for
  older versions of Python.

1.47.0
------

* Use ``pytest<5.0.0`` until gabbi has solutions for the changes in ``5.0.0``.

1.46.0
------

* A ``-q`` argument is added to :doc:`gabbi-run <runner>` to suppress output
  from the test runner.

1.45.0
------

* Adjust loading of YAML to be ready for new release of PyYAML.

1.44.0
------

* Provide the
  :class:`~gabbi.handlers.yaml_disk_loading_jsonhandler.YAMLDiskLoadingJSONHandler`
  class that allows test result data for ``response_json_path``
  checks to be loaded from YAML-on-disk.

1.43.0
------

* Use :ref:`jsonpath` to select a portion of data-on-disk in
  ``response_json_path`` checks.
* Restrict PyYAML to ``<4.0``.

1.42.0
------

* Allow listing of tests with no host configured. When host is
  an empty string, tests can be listed (for discovery), but will
  be skipped on run.

1.41.0
------

* JSON ``$RESPONSE`` :ref:`substitutions <state-substitution>` in
  the ``data`` field may be complex types (lists and dicts), not
  solely strings.

1.40.0
------

* When the HTTP response begins with a bad status line, have
  BadStatusLine be raised from urllib3.

1.39.0
------

* Allow :ref:`substitutions <state-substitution>` in the key portion
  of request and response headers, not just the value.

1.38.0
------

* Remove support for Python 3.3.
* Make handling of fixture-level skips in pytest actually work.

1.37.0
------

* Add ``safe_yaml`` parameter to :meth:`~gabbi.driver.build_tests`.

1.36.0
------

* ``use_prior_test`` is added to test :ref:`metadata`.
* Extensive cleanups in regular expression handling when constructing
  tests from YAML.

1.35.0
------

:doc:`jsonpath` handling gets two improvements:

* The value side of a ``response_json_paths`` entry can be loaded
  from a file using the ``<@file.json`` syntax also used in
  :ref:`data`.
* The key side of a ``response_json_paths`` entry can use
  :ref:`substitutions <state-substitution>`. This was already true
  for the value side.

1.34.0
------

:ref:`Substitutions <state-substitution>` in ``$RESPONSE`` handling
now preserve numeric types instead of casting to a string. This is
useful when servers are expecting strong types and tests want to
send response data back to the server.

1.33.0
------

``count`` and ``delay`` test keys allow :ref:`substitutions
<state-substitution>`. :meth:`gabbi.driver.build_tests` accepts
a ``verbose`` parameter to set test :ref:`verbosity <metadata>` for
an entire session.

1.32.0
------

Better failure reporting when using :doc:`gabbi-run <runner>` with
multiple files. Test names are based on the files and a summary of
failed files is provided at the end of the report.

1.31.0
------

Effectively capture a failure in a :doc:`fixture <fixtures>` and
report the traceback. Without this some test runners swallow the
error and discovering problems when developing fixtures can be quite
challenging.

1.30.0
------

Thanks to Samuel Fekete, tests can use the ``$HISTORY`` dictionary
to refer to any prior test in the same file, not just the one
immediately prior, when doing :ref:`substitutions <state-substitution>`.

1.29.0
------

Filenames used to read data into tests using the ``<@`` syntax
may now use pathnames relative to the YAML file. See :ref:`data`.

:doc:`gabbi-run <runner>` gains a --verbose parameter to force
all tests run in a session to run with :ref:`verbose <metadata>`
set.

When using :ref:`pytest <pytest_loader>` to load tests, a new
mechanism is available which avoids warnings produced in when using
a version of pytest greater than ``3.0``.

1.28.0
------

When verbosely displaying request and response bodies that are
JSON, pretty print for improved readability.

1.27.0
------

Allow :doc:`gabbi-run <runner>` to accept multiple filenames as
command line arguments instead of reading tests from stdin.

1.26.0
------

Switch from response handlers to :doc:`handlers` to allow more
flexible processing of both response _and_ request bodies.

Add :ref:`inner fixtures <inner-fixtures>` for per test fixtures,
useful for output capturing.

1.25.0
------

Allow the ``test_loader_name`` arg to
:meth:`gabbi.driver.build_tests` to override the prefix of the
pretty printed name of generated tests.

1.24.0
------

String values in JSONPath matches may be wrapped in ``/.../``` to be
treated as regular expressions.

1.23.0
------

Better :doc:`documentation <loader>` of how to run gabbi in a
concurrent environment. Improved handling of pytest fixtures and
test counts.

1.22.0
------

Add ``url`` to :meth:`gabbi.driver.build_tests` to use instead of
``host``, ``port`` and ``prefix``.

1.21.0
------

Add ``require_ssl`` to :meth:`gabbi.driver.build_tests` to force use
of SSL.

1.20.0
------

Add ``$COOKIE`` :ref:`substitution <state-substitution>`.

1.19.1
------

Correctly support IPV6 hosts.

1.19.0
------

Add ``$LAST_URL`` :ref:`substitution <state-substitution>`.

1.17.0
------

Introduce support for loading and running tests with pytest.

1.16.0
------

Use urllib3 instead of httplib2 for driving HTTP requests.

1.13.0
------

Add sorting and filtering to :doc:`jsonpath` handling.

1.11.0
------

Add the ``response_forbidden_headers`` to :ref:`response expectations
<response-expectations>`.

1.7.0
-----

.. highlight:: yaml

Instead of::

    tests:
    - name: a simple get
      url: /some/path
      method: get

1.7.0 also makes it possible to::

    tests:
    - name: a simple get
      GET: /some/path

Any upper case key is treated as a method.

1.4.0 and 1.5.0
---------------

Enhanced flexibility and colorization when setting tests to be
:ref:`verbose <metadata>`.

1.3.0
-----

Adds the ``query_parameters`` key to :ref:`request parameters
<request-parameters>`.

1.2.0
-----

The start of improvements and extensions to :doc:`jsonpath`
handling. In this case the addition of the ``len`` function.

1.1.0
-----

Vastly improved output and behavior in :doc:`gabbi-run <runner>`.

1.0.0
-----

Version 1 was the first release with a commitment to a stable
:doc:`format`. Since then new fields have been added but have not
been taken away.

Contributors
============

The following people have contributed code to gabbi. Thanks to them.
Thanks also to all the people who have made gabbi better by
reporting issues_ and their successes and failures with using
gabbi.

* Chris Dent
* FND
* Mehdi Abaakouk
* Tom Viner
* Jason Myers
* Josh Leeb-du Toit
* Duc Truong
* Zane Bitter
* Ryan Spencer
* Kim Raymoure
* Travis Truman
* Samuel Fekete
* Michael McCune
* Imran Hayder
* Julien Danjou
* Trevor McCasland
* Danek Duvall
* Marc Abramowitz

.. _commit logs: https://github.com/cdent/gabbi/commits
.. _issues: https://github.com/cdent/gabbi/issues
