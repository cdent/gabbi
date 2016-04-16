Test Example
============

What follows is a commented example of some tests in a single
file demonstrating many of the :doc:`format` features. See
`Loader`_, below, for the Python needed to integrate with a testing
harness.

.. literalinclude:: example.yaml
   :language: yaml

.. _test_loaders:

Loader
------

To run the tests they must be generated in some fashion and then
run. This is accomplished by a test loader. Initially gabbi only
supported those test harnesses that supported the ``load_tests``
protocol in UnitTest. It now possible to also build and run tests
with pytest_ with some limitations described below.

UnitTest Style Loader
~~~~~~~~~~~~~~~~~~~~~

To run the tests with a ``load_tests`` style loader a test file containing
a ``load_tests`` method is required. That will look a bit like:

.. literalinclude:: example.py
   :language: python

For details on the arguments available when building tests see
:meth:`~gabbi.driver.build_tests`.

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
advanced options, including using ``testrepository`` and
``subunit``.

pytest
~~~~~~

Since pytest does not support the ``load_tests`` system, a different
way of generating tests is required. A test file must be created
that calls :meth:`~gabbi.driver.py_test_generator` and yields the
generated tests. That will look a bit like this:

.. literalinclude:: pytest-example.py
   :language: python

This can then be run with the usual pytest commands. For example::

   py.test -svx pytest-example.py

.. _source distribution: https://github.com/cdent/gabbi
.. _the tutorial repo: https://github.com/cdent/gabbi-demo
.. _pytest: http://pytest.org/
