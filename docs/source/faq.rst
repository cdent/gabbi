
Frequently Asked Questions
==========================

.. note:: This section provides a collection of questions with
          answers that don't otherwise fit in the rest of the
          documentation. If something is missing, please create an
          issue_.

          As this document grows it will gain a more refined
          structure.

General
~~~~~~~

Is gabbi only for testing Python-based APIs?
--------------------------------------------

No, you can use :doc:`gabbi-run <runner>` to test an HTTP service
built in any programming language.

Testing Style
~~~~~~~~~~~~~

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

