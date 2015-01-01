.. Gabbi documentation master file, created by
   sphinx-quickstart on Wed Dec 31 17:07:32 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :maxdepth: 1
   :hidden:

   format
   host
   fixtures
   gabbi

Gabbi
=====

Gabbi is a tool for running HTTP tests where requests and responses
are expressed as declarations in a collection of YAML files.

If you're not after the overview and just want to get on with it,
see the :doc:`gabbi` documentation and the test files in the
`source distribution`_.

The name is derived from "gabby": excessively talkative. In a test
environment this is a good thing. The "y" to an "i" is an
optimization for any future backronyms.

.. _source distribution: https://github.com/cdent/gabbi

Purpose
-------

Gabbi works to bridge the gap between human readable YAML files (see
:doc:`format` for details) that represent HTTP requests and expected
responses and the obscured realm of Python-based, object-oriented unit
tests in the style of the unittest module and its derivatives.

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

Extended functionality, such as the use of `JSONPath`_ to query response
bodies and reuse the prior response data in the current request,
exists to make it easier to test relatively complex JSON-driven APIs,
even those bold enough to lay claim to being fully RESTful with
HATEOAS.

This functionality should not be taken as license to write gloriously
complex test files. If your API is so complex that it needs complex
test files then you may wish to take that as a sign that your API
itself too complex.

.. _JSONPath: http://goessner.net/articles/JsonPath/
