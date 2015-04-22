.. Gabbi documentation master file, created by
   sphinx-quickstart on Wed Dec 31 17:07:32 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :maxdepth: 1
   :hidden:

   format
   example
   host
   fixtures
   handlers
   runner
   gabbi

Gabbi
=====

Gabbi is a tool for running HTTP tests where requests and responses
are expressed as declarations in a collection of YAML files.

The name is derived from "gabby": excessively talkative. In a test
environment having visibility of what a test is actually doing is a
good thing. The "y" to an "i" is an optimization for as yet to be
determined backronyms such as: "Garrulous API Barrier Breaking
Initiative" or "Glorious And Basic Beta Investigator". These
are not good enough so the search continues.

If you want to get straight to creating tests look at
:doc:`example`, the test files in the `source distribution`_
and :doc:`format`. A full tutorial is in the works.

.. _source distribution: https://github.com/cdent/gabbi

Purpose
-------

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
