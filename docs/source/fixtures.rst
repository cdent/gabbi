Fixtures
========

Each suite of tests is represented by a single YAML file, and may
optionally use one or more fixtures to provide the necessary
environment required by the tests in that file.

Fixtures are implemented as nested context managers. Subclasses
of :class:`~gabbi.fixture.GabbiFixture` must implement
``start_fixture`` and ``stop_fixture`` methods for creating and
destroying, respectively, any resources managed by the fixture.
While the subclass may choose to implement ``__init__`` it is
important that no exceptions are thrown in that method, otherwise
the stack of context managers will fail in unexpected ways. Instead
initialization of real resources should happen in ``start_fixture``.

At this time there is no mechanism for the individual tests to have any
direct awareness of the fixtures. The fixtures exist, conceptually, on
the server side of the API being tested.

Fixtures may do whatever is required by the testing environment,
however there are two common scenarios:

* Establishing (and then resetting when a test suite has finished) any
  baseline configuration settings and persistence systems required for
  the tests.
* Creating sample data for use by the tests.

If a fixture raises ``unittest.case.SkipTest`` during
``start_fixture`` all the tests in the current file will be skipped.
This makes it possible to skip the tests if some optional
configuration (such as a particular type of database) is not
available.

If an exception is raised while a fixture is being used, information
about the exception will be stored on the fixture so that the
``stop_fixture`` method can decide if the exception should change how
the fixture should clean up. The exception information can be found on
``exc_type``, ``exc_value`` and ``traceback`` method attributes.

If an exception is raised when a fixture is started (in
``start_fixture``) the first test in the suite using the fixture
will be marked with an error using the traceback from the exception
and all the tests in the suite will be skipped. This ensures that
fixture failure is adequately captured and reported by test runners.

.. _inner-fixtures:

Inner Fixtures
==============

In some contexts (for example CI environments with a large
number of tests being run in a broadly concurrent environment where
output is logged to a single file) it can be important to capture and
consolidate stray output that is produced during the tests and display
it associated with an individual test. This can help debugging and
avoids unusable output that is the result of multiple streams being
interleaved.

Inner fixtures have been added to support this. These are fixtures
more in line with the tradtional ``unittest`` concept of fixtures:
a class on which ``setUp`` and ``cleanUp`` is automatically called.

:func:`~gabbi.driver.build_tests` accepts a named parameter
arguments of ``inner_fixtures``. The value of that argument may be
an ordered list of fixtures.Fixture_ classes that will be called
when each individual test is set up.

An example fixture that could be useful is the FakeLogger_.

.. note:: At this time ``inner_fixtures`` are not supported when
          using the pytest :doc:`loader <loader>`.

.. _fixtures.Fixture: https://pypi.python.org/pypi/fixtures
.. _FakeLogger: https://pypi.python.org/pypi/fixtures#fakelogger
