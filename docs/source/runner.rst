YAML Runner
===========

If there is a running web service that needs to be tested and
creating a test loader with :meth:`~gabbi.driver.build_tests` is
either inconvenient or overkill it is possible to run YAML test
files directly from the command line with the console-script
``gabbi-run``. It accepts YAML on ``stdin`` or as multiple file
arguments, and generates and runs tests and outputs a summary of
the results.

The provided YAML may not use custom :doc:`fixtures` but otherwise
uses the default :doc:`format`. :doc:`host` information is either
expressed directly in the YAML file or provided on the command
line::

    gabbi-run [host[:port]] < /my/test.yaml

or::

    gabbi-run http://host:port < /my/test.yaml

To test with one or more files the following command syntax may be
used::

    gabbi-run http://host:port -- /my/test.yaml /my/other.yaml

.. note:: The filename arguments must come after a ``--`` and all
          other arguments (host, port, prefix, failfast) must come
          before the ``--``.

To facilitate using the same tests against the same application mounted
in different locations in a WSGI server, a ``prefix`` may be provided
as a second argument::

    gabbi-run host[:port] [prefix] < /my/test.yaml

or in the target URL::

    gabbi-run http://host:port/prefix < /my/test.yaml

The value of prefix will be prepended to the path portion of URLs that
are not fully qualified.

Anywhere host is used, if it is a raw IPV6 address it should be
wrapped in ``[`` and ``]``.

If ``https`` is used in the target, then the tests in the provided
YAML will default to ``ssl: True``.

If a ``-x`` or ``--failfast`` argument is provided then ``gabbi-run`` will
exit after the first test failure.

Use ``-v`` or ``--verbose`` with a value of ``all``, ``headers`` or ``body``
to turn on :ref:`verbosity <metadata>` for all tests being run.
