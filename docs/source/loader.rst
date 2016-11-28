
Loading and Running Tests
=========================

.. _test_loaders:

To run gabbi tests with a test harness they must be generated in
some fashion and then run. This is accomplished by a test loader.
Initially gabbi only supported those test harnesses that supported
the ``load_tests`` protocol in UnitTest. It now possible to also
build and run tests with pytest_ with some limitations described below.

.. note:: It is also possible to run gabbi tests from the command
          line. See :doc:`runner`.

.. warning:: If test are being run with a runner that supports
             concurrency (such as ``testrepository``) it is critical
             that the test runner is informed of how to group the
             tests into their respective suites. The usual way to do
             this is to use a regular expression that groups based
             on the name of the yaml files. For example, when using
             ``testrepository`` the ``.testr.conf`` file needs an
             entry similar to the following::

                 group_regex=gabbi\.suitemaker\.(test_[^_]+_[^_]+)

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

.. _pytest_loader:

Since pytest does not support the ``load_tests`` system, a different
way of generating tests is required. Two techniques are supported.

The original method (described below) used yield statements to
generate tests which pytest would collect. This style of tests is
deprecated as of ``pytest>=3.0`` so a new style using pytest
fixtures has been developed.

pytest >= 3.0
-------------

In the newer technique, a test file is created that uses the
``pytest_generate_tests`` hook. Special care must be taken to always
import the ``test_pytest`` method which is the base test that the
pytest hook parametrizes to generate the tests from the YAML files.
Without the method, the hook will not be called and no tests generated.

Here is a simple example file:

.. literalinclude:: pytest3.0-example.py
   :language: python

This can then be run with the usual pytest commands. For example::

   py.test -svx pytest3.0-example.py

pytest < 3.0
------------

When using the older technique, test file must be created
that calls :meth:`~gabbi.driver.py_test_generator` and yields the
generated tests. That will look a bit like this:

.. literalinclude:: pytest-example.py
   :language: python

This can then be run with the usual pytest commands. For example::

   py.test -svx pytest-example.py

The older technique will continue to work with all versions of
``pytest<4.0`` but ``>=3.0`` will produce warnings. If you want to
use the older technique but not see the warnings add
``--disable-pytest-warnings`` parameter to the invocation of
``py.test``.

.. _source distribution: https://github.com/cdent/gabbi
.. _the tutorial repo: https://github.com/cdent/gabbi-demo
.. _pytest: http://pytest.org/
