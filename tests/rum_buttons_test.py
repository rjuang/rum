import sys
import unittest

sys.path.insert(0, '..')
from rum_buttons import Button
from rum_threading import Scheduler
from tests.testutils import FakeClock

class ButtonsTests(unittest.TestCase):
    def setUp(self):
        self._clock = FakeClock()
        self._scheduler = Scheduler(time_fn=self._clock.time)
        self._button = Button(self._scheduler)

        self._long_count = 0
        self._short_count = 0

        def inc_long_count():
            self._long_count += 1

        def inc_short_count():
            self._short_count += 1

        self._button.set_short_press(inc_short_count)
        self._button.set_long_press(inc_long_count)

    def test_shortPress_buttonWithListeners_listenersTrigger(self):
        self._button.notify_touch()
        self._button.notify_touch(release=True)

        self.assertEqual(1, self._short_count)
        self._clock.advance(1)
        self._scheduler.idle()
        self.assertEqual(0, self._long_count)

    def test_longPress_buttonWithListeners_listenersTrigger(self):
        self._long_count = 0
        self._short_count = 0

        self._button.notify_touch()
        self._clock.advance(1)
        self._scheduler.idle()
        self._button.notify_touch(release=True)

        self.assertEqual(0, self._short_count)
        self.assertEqual(1, self._long_count)

    def test_shortPress_buttonWithLongPressListenerOnly_noTrigger(self):
        self._button.set_short_press(None)
        self._button.notify_touch()
        self._button.notify_touch(release=True)

        self.assertEqual(0, self._short_count)
        self.assertEqual(0, self._long_count)

    def test_longPress_buttonWithShortPressListenerOnly_noTrigger(self):
        self._button.set_long_press(None)
        self._button.notify_touch()
        self._clock.advance(1)
        self._scheduler.idle()
        self._button.notify_touch(release=True)

        self.assertEqual(0, self._short_count)
        self.assertEqual(0, self._long_count)


if __name__ == '__main__':
    unittest.main()
