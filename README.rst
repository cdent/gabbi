gabbi
=====

Gabbi is a tool for running HTTP tests where requests and responses
are represented in a declarative form.

It is currently under development and does not yet work (it will
create TestSuites from YAML files, but not yet execute any http
requests).

Purpose
-------

Gabbi works to bridge the gap between human readable YAML files that
represent HTTP requests and expected responses and the obscured realm of
Python-based, object-oriented unit tests in the style of the unittest
module and its derivatives.

Each YAML file represents an order list of HTTP requests along with
the expected responses. This allows a single file to represent a
process in the API, not just a single request in isolation. For
example:

* Create a resource.
* Retrieve a resource.
* Delete a resource.
* Retrieve a resource again to confirm it is gone.

At the same time it is still possible to ask gabbi to run just one
request. If it is in a sequence of tests, those tests prior to it in
the YAML file will be run (in order). In any single process any test
will only be run once. Concurrency is handled such that one file
runs in one process.

The features mean that it is possible to create tests that are
useful for both humans (as tools for improving and developing APIs)
and automated CI systems.

To Do
-----

* [ ] Do the actual HTTP requesting and response evaluation.
* [ ] Enable optional use of wsgi-intercept so no web server is required.
* [ ] Consider fixture management (data store) per YAML file.
* [ ] Dealing with driving authN and authZ.
