"""Manage fixtures for gabbi at the test file level."""


def start_fixture(fixture_class):
    """Create the fixture class and start it."""
    fixture = fixture_class()
    fixture.start()


def stop_fixture(fixture_class):
    """Create the fixture class and stop it."""
    fixture = fixture_class()
    fixture.stop()


class GabbiFixture(object):
    """A singleton of a fixture."""

    _instance = None
    _started = False
    _halted = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GabbiFixture, cls).__new__(cls)
        return cls._instance

    def start(self):
        if not self._started and not self._halted:
            self._started = True
            self.start_fixture()

    def start_fixture(self):
        pass

    def stop(self):
        if self._started:
            self.stop_fixture()
        self._started = False
        self._halted = True

    def stop_fixture(self):
        pass
