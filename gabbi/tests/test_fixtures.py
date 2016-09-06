#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""Use mocks to confirm that fixtures operate as context managers.
"""

from six.moves import mock
import unittest

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


class FixtureTest(unittest.TestCase):

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
