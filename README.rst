.. image:: https://travis-ci.org/cdent/gabbi.svg?branch=master
    :target: https://travis-ci.org/cdent/gabbi
.. image:: https://readthedocs.org/projects/gabbi/badge/?version=latest
    :target: https://gabbi.readthedocs.io/en/latest/
    :alt: Documentation Status

Gabbi
=====

`Release Notes`_

Gabbi is a tool for running HTTP tests where requests and responses
are represented in a declarative YAML-based form. The simplest test
looks like this::

    tests:
    - name: A test
      GET: /api/resources/id

See the docs_ for more details on the many features and formats for
setting request headers and bodies and evaluating responses.

Gabbi is tested with Python 2.7, 3.4, 3.5, 3.6 and pypy.

Tests can be run using `unittest`_ style test runners, `pytest`_
or from the command line with a `gabbi-run`_ script.

There is a `gabbi-demo`_ repository which provides a tutorial via
its commit history. The demo builds a simple API using gabbi to
facilitate test driven development.

.. _Release Notes: https://gabbi.readthedocs.io/en/latest/release.html
.. _docs: https://gabbi.readthedocs.io/
.. _gabbi-demo: https://github.com/cdent/gabbi-demo
.. _unittest: https://gabbi.readthedocs.io/en/latest/example.html#loader
.. _pytest: http://pytest.org/
.. _loader docs: https://gabbi.readthedocs.io/en/latest/example.html#pytest
.. _gabbi-run: https://gabbi.readthedocs.io/en/latest/runner.html

Purpose
-------

Gabbi works to bridge the gap between human readable YAML files that
represent HTTP requests and expected responses and the obscured realm of
Python-based, object-oriented unit tests in the style of the unittest
module and its derivatives.

Each YAML file represents an ordered list of HTTP requests along with
the expected responses. This allows a single file to represent a
process in the API being tested. For example:

* Create a resource.
* Retrieve a resource.
* Delete a resource.
* Retrieve a resource again to confirm it is gone.

At the same time it is still possible to ask gabbi to run just one
request. If it is in a sequence of tests, those tests prior to it in
the YAML file will be run (in order). In any single process any test
will only be run once. Concurrency is handled such that one file
runs in one process.

These features mean that it is possible to create tests that are
useful for both humans (as tools for improving and developing APIs)
and automated CI systems.

Testing
-------

To run the built in tests (the YAML files are in the directories
``gabbi/gabbits_*`` and loaded by the file ``gabbi/test_*.py``),
you can use ``tox``::

    tox -epep8,py27,py34

Or if you have the dependencies installed (or a warmed up
virtualenv) you can run the tests by hand and exit on the first
failure::

    python -m subunit.run discover -f gabbi | subunit2pyunit

Testing can be limited to individual modules by specifying them
after the tox invocation::

    tox -epep8,py27,py34 -- test_driver test_handlers

If you wish to avoid running tests that connect to internet hosts,
set ``GABBI_SKIP_NETWORK`` to ``True``.
