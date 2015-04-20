Test Example
============

What follows is a commented example of some tests in a single
file demonstrating many of the :doc:`format` features. See
`Loader`_, below, for the Python need to integrate with a testing
harness.

.. literalinclude:: example.yaml
   :language: yaml

Loader
------

To run those tests a test loader is required. That would look a
bit like this:

.. literalinclude:: example.py
   :language: python
