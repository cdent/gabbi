Target Host
===========

The target host is the host on which the API to be tested can be found.
Gabbi intends to preserve the flow and semantics of HTTP interactions
as much as possible, and every HTTP request needs to be directed at a host
of some form. Gabbi provides three ways to control this:

* Using `WSGITransport` of httpx to provide a ``WSGI`` environment on
  directly attached to a ``WSGI`` application (see `intercept examples`_).
* Using fully qualified ``url`` values in the YAML defined tests (see
  `full examples`_).
* Using a host and (optionally) port defined at test build time (see
  `live examples`_).

The intercept and live methods are mutually exclusive per test builder,
but either kind of test can freely intermix fully qualified URLs into the
sequence of tests in a YAML file.

For Python-based test driven development and local tests the intercept
style of testing lowers test requirements (no web server required) and
is fast. Interception is performed as part of the per-test-case http
client. Configuration or database setup may be performed using
:doc:`fixtures`.

For the implementation of the above see :meth:`~gabbi.driver.build_tests`.

.. _WSGITransport: https://www.python-httpx.org/advanced/transports/#wsgi-transport
.. _intercept examples: https://github.com/cdent/gabbi/blob/main/gabbi/tests/test_intercept.py
.. _full examples: https://github.com/cdent/gabbi/blob/main/gabbi/tests/gabbits_live/google.yaml
.. _live examples: https://github.com/cdent/gabbi/blob/main/gabbi/tests/test_live.py
