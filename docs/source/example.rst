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

Once the test loader has been created, it needs to be run. There are *many*
options. Which is appropriate depends very much on your environment. Here are
some examples using ``unittest`` or ``testtools`` that require minimal
knowledge to get started.

By file::

    python -m testtools.run -v test/test_loader.py

By module::

    python -m testttols.run -v test.test_loader

    python -m unittest -v test.test_loader

Using test discovery to locate all tests in a directory tree::

    python -m testtools.run discover

    python -m unittest discover test

See the `source distribution`_ and `the tutorial repo`_ for more
advanced options.

.. _source distribution: https://github.com/cdent/gabbi
.. _the tutorial repo: https://github.com/cdent/gabbi-demo
