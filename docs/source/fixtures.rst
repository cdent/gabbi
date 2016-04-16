Fixtures
========

Each suite of tests is represented by a single YAML file, and may
optionally use one or more fixtures to provide the necessary
environment for tests to run.

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
