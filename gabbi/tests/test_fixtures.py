"""
Use mocks to confirm that fixtures operate as context managers.
"""

import mock
import testtools

from gabbi import fixture


class FakeFixture(fixture.GabbiFixture):

    def __init__(self, mock):
        super(FakeFixture, self).__init__()
        self.mock = mock

    def start_fixture(self):
        self.mock.start()

    def stop_fixture(self):
        if self.exc_type:
            self.mock.handle(self.exc_type)
        self.mock.stop()


class FixtureTest(testtools.TestCase):

    def setUp(self):
        super(FixtureTest, self).setUp()
        self.magic = mock.MagicMock(['start', 'stop', 'handle'])

    def test_fixture_starts_and_stop(self):
        with FakeFixture(self.magic):
            pass
        self.magic.start.assert_called_once_with()
        self.magic.stop.assert_called_once_with()

    def test_fixture_informs_on_exception(self):
        """Test that the stop fixture is passed exception info."""
        try:
            with FakeFixture(self.magic):
                raise ValueError()
        except ValueError:
            pass
        self.magic.start.assert_called_once_with()
        self.magic.stop.assert_called_once_with()
        self.magic.handle.assert_called_once_with(ValueError)
