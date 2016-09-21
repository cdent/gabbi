
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

Workarounds
~~~~~~~~~~~

pytest produces warnings about yield tests. Can I make them stop?
-----------------------------------------------------------------

Yes, run as ``py.test --disable-pytest-warnings`` to quiet the
warnings. Or use a version of pytest less than ``3.0``. For more details
see :ref:`pytest <pytest_loader>`.

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

