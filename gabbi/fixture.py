"""Manage fixtures for gabbi at the test file level."""


def start_fixture(fixture_class):
    """Create the fixture class and start it."""
    fixture = fixture_class()
    fixture.start()


def stop_fixture(fixture_class):
    """Re-Create the fixture class and stop it."""
    fixture = fixture_class()
    fixture.stop()


class GabbiFixtureError(Exception):
    """Generic exception for GabbiFixture."""
    pass


class GabbiFixture(object):
    """A singleton of a fixture.

    Subclasses must implement start_fixture and stop_fixture, each of which
    contain the logic for stopping and starting whatever the fixture is.
    What a fixture is is left as an exercise for the implementor.

    A singleton is used so as to avoid in process duplication of the same
    fixture. For environments where concurrent testing will be used, the
    fixture should guard against collisions by uniquifying filenames,
    database names and other external resources.

    If calling code attempts to start an already started fixture, an Exception
    will be raised: GabbiFixtureError.
    """

    _instance = None
    _started = False

    def __new__(cls, *args, **kwargs):
        """Create the new instance or return an existing one."""
        if not cls._instance:
            cls._instance = super(GabbiFixture, cls).__new__(cls)
        return cls._instance

    def start(self):
        """Request that the fixture be started."""
        if not self._started:
            self.start_fixture()
            self._started = True
        else:
            raise GabbiFixtureError('fixture %s already started' % self)

    def start_fixture(self):
        """Implement the actual workings of starting the fixture here."""
        pass

    def stop(self):
        """Request that the fixture be stopped."""
        if self._started:
            self.stop_fixture()
        self._started = False

    def stop_fixture(self):
        """Implement the actual workings of stopping the fixture here."""
        pass
