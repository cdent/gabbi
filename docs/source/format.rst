Test Format
===========

Gabbi tests are expressed as YAML containing an HTTP request and an
expected response. Each YAML file is an ordered sequence of requests.
The bare minimum YAML file for a single request is:::

    tests:
       - name: the name of a test
         url: /

This will make a request to ``/`` on whatever the configured
:doc:`host` is. The test will pass if the status of the HTTP response
is ``200``.

The ``tests`` key can contain as many requests, in sequence, as
required. Other top level keys are:

* fixtures: A sequence of named :doc:`fixtures`.
* defaults: A dictionary of local default values for the requests and
  responses in the ``tests`` in this file. These override the global
  defaults (explained below).

Each test can use the following structure. Only ``name`` and ``url``
are required.

* To be written. In the meantime see `some of the gabbi tests`_.

.. _some of the gabbi tests: https://github.com/cdent/gabbi/tree/master/gabbi/gabbits_intercept
