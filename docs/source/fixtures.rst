Fixtures
========

In gabbi, fixtures are implemented as nested context managers. Subclasses
of :class:`~gabbi.fixture.GabbiFixture` must implement 
``start_fixture`` and ``stop_fixture`` methods creating and
destroying, respectively, any resources managed by the fixture.
While the subclass may choose to implement ``__init__`` it is
important that no exceptions are thrown in that method, otherwise
the stack of context managers will fail in unexpected ways. Instead
initialization of real resources should happen in ``start_fixture``.

At this time there is no mechanism for the individual tests to have
any direct awareness of the fixtures. The fixtures exist, instead, on the
inside of the API being tested. Their most common function is
expected to be the creation of sample data, by whatever means make
sense for the system being tested.
