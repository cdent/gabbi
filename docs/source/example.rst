Test Example
============

What follows is a commented example of some tests in a single
file demonstrating many of the :doc:`format` features. See
`Loader`_, below, for the Python needed to integrate with a testing
harness.

.. literalinclude:: example.yaml
   :language: yaml

Loader
------

Test Loader
~~~~~~~~~~~

To run those tests a test loader is required. That would look a
bit like this:

.. literalinclude:: example.py
   :language: python

Run Test Loader
~~~~~~~~~~~~~~~
There are *many* options. This outlines two that require minimal knowledge to get started.

testtools
_________
By file:
python -m testtools.run -v test/test_loader.py

By module:
python -m testttols.run -v test.test_loader

unittest
________

python -m unittest -v test_loader
