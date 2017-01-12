
Frequently Asked Questions
==========================

.. note:: This section provides a collection of questions with
          answers that don't otherwise fit in the rest of the
          documentation. If something is missing, please create an
          issue_.

          As this document grows it will gain a more refined
          structure.

.. highlight:: yaml

General
~~~~~~~

Is gabbi only for testing Python-based APIs?
--------------------------------------------

No, you can use :doc:`gabbi-run <runner>` to test an HTTP service
built in any programming language.

How do I run just one test?
---------------------------

Each YAML file contains a sequence of tests, each test within each file has a
name. That name is translated to the name of the test by replacing spaces with
an ``_``.

When running tests that are :doc:`generated dynamically <loader>`, filtering
based on the test name prior to the test being collected will not work in some
test runners.  Test runners that use a ``--load-list`` functionality can be
convinced to filter after discovery.

`pytest` does this directly with the ``-k`` keyword flag.

When using testrepository with tox as used in gabbi's own tests it is possible
to pass a filter in the tox command::

    tox -epy27 -- get_the_widget

When using ``testtools.run`` and similar test runners it's a bit more
complicated. It is necessary to provide the full name of the test as a list to
``--load-list``::

    python -m testtools.run --load-list \
        <(echo package.tests.test_api.yamlfile_get_the_widge.test_request)

Testing Style
~~~~~~~~~~~~~

Can I have variables in my YAML file?
-------------------------------------

Gabbi provides the ``$ENVIRON`` :ref:`substitution
<state-substitution>` which can operate a bit like variables that
are set elsewhere and then used in the tests defined by the YAML.

If you find it necessary to have variables within a single YAML file
you take advantage of YAML `alias nodes`_ list this::

    vars:
      - &uuid_1 5613AABF-BAED-4BBA-887A-252B2D3543F8

    tests:
    - name: send a uuid to a post
      POST: /resource
      request_headers:
        content-type: application/json
      data:
        uuid: *uuid_1

You can alias all sorts of nodes, not just single items. Be aware
that the replacement of an alias node happens while the YAML is
being loaded, before gabbi does any processing.

.. _alias nodes: http://www.yaml.org/spec/1.2/spec.html#id2786196

How many tests should be put in one YAML file?
----------------------------------------------

For the sake of readability it is best to keep each YAML file
relatively short. Since each YAML file represents a sequence of
requests, it usually makes sense to create a new file when a test is
not dependent on any before it.

It's tempting to put all the tests for any resource or URL in the
same file, but this eventually leads to files that are too long and
are thus difficult to read.

.. _issue: https://github.com/cdent/gabbi/issues

