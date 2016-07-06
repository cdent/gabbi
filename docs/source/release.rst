Release Notes
=============

These are informal release notes for gabbi since version 1.0.0,
highlighting major features and changes. For more detail see
the `commit logs`_ on GitHub.

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
* Jason Myers
* Kim Raymoure
* Michael McCune
* Imran Hayder
* Julien Danjou
* Marc Abramowitz

.. _commit logs: https://github.com/cdent/gabbi/commits
.. _issues: https://github.com/cdent/gabbi/issues
