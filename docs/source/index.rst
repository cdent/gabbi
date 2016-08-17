.. Gabbi documentation master file, created by
   sphinx-quickstart on Wed Dec 31 17:07:32 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :maxdepth: 1
   :hidden:

   format
   loader
   example
   jsonpath
   host
   fixtures
   handlers
   runner
   release
   faq
   gabbi

Gabbi
=====

.. highlight:: yaml

Gabbi is a tool for running HTTP tests where requests and responses
are expressed as declarations in a collection of YAML files. The
simplest test looks like this::

    tests:
    - name: A test
      GET: /api/resources/id

See the rest of these docs for more details on the many features and
formats for setting request headers and bodies and evaluating responses.

The name is derived from "gabby": excessively talkative. In a test
environment having visibility of what a test is actually doing is a
good thing. This is especially true when the goal of a test is to
test the HTTP, not the testing infrastructure. Gabbi tries to put
the HTTP interaction in the foreground of testing.

Tests can be run using :ref:`unittest <test_loaders>` style test
runners or py.test or from the command line with a :doc:`gabbi-run <runner>` script.

If you want to get straight to creating tests look at
:doc:`example`, the test files in the `source distribution`_
and :doc:`format`. A `gabbi-demo`_ repository provides a tutorial
of using gabbi to build an API, via the commit history of the repo.

.. _source distribution: https://github.com/cdent/gabbi
.. _gabbi-demo: https://github.com/cdent/gabbi-demo

Purpose
-------

.. highlight:: none

Gabbi works to bridge the gap between human readable YAML files (see
:doc:`format` for details) that represent HTTP requests and expected
responses and the rather complex world of automated testing.

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
will only be run once. Concurrency is handled such that one file runs
in one process.

These features mean that it is possible to create tests that are useful
for both humans (as tools for learning, improving and developing APIs)
and automated CI systems.

Significant flexibility and power is available in the :doc:`format` to
make it relatively straightforward to test existing complex APIs.
This extended functionality includes the use of `JSONPath`_ to query
response bodies and templating of test data to allow access to the prior
HTTP response in the current request. For APIs which do not use JSON
additional :doc:`handlers` can be created.

Care should be taken when using this functionality when you are
creating a new API. If your API is so complex that it needs complex
test files then you may wish to take that as a sign that your API
itself too complex. One goal of gabbi is to encourage transparent
and comprehensible APIs.

Though gabbi is written in Python and under the covers uses
``unittest`` data structures and processes, there is no requirement
that the :doc:`host` be a Python-based service. Anything talking
HTTP can be tested. A :doc:`runner` makes it possible to simply
create YAML files and point them at a running server.

.. _JSONPath: http://goessner.net/articles/JsonPath/
