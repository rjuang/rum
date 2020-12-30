import os
import sys
import time
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rum_buttons import Button
from rum_threading import Scheduler


class ButtonsTests(unittest.TestCase):
    def test_shortPress_buttonWithListeners_listenersTrigger(self):
        scheduler = Scheduler()
        button = Button(scheduler)
        self._long_count = 0
        self._short_count = 0

        def inc_long_count():
            self._long_count += 1

        def inc_short_count():
            self._short_count += 1

        button.set_short_press(inc_short_count)
        button.set_long_press(inc_long_count)
        button.notify_touch()
        button.notify_touch(release=True)

        self.assertEqual(1, self._short_count)
        scheduler.idle(override_time=time.monotonic() + 1)
        self.assertEqual(0, self._long_count)

    def test_longPress_buttonWithListeners_listenersTrigger(self):
        scheduler = Scheduler()
        button = Button(scheduler)
        self._long_count = 0
        self._short_count = 0

        def inc_long_count():
            self._long_count += 1

        def inc_short_count():
            self._short_count += 1

        button.set_short_press(inc_short_count)
        button.set_long_press(inc_long_count)

        button.notify_touch()
        scheduler.idle(override_time=time.monotonic() + 1)
        button.notify_touch(release=True)

        self.assertEqual(0, self._short_count)
        self.assertEqual(1, self._long_count)

    def test_shortPress_buttonWithLongPressListenerOnly_noTrigger(self):
        scheduler = Scheduler()
        button = Button(scheduler)
        self._long_count = 0
        self._short_count = 0

        def inc_long_count():
            self._long_count += 1

        button.set_short_press(None)
        button.set_long_press(inc_long_count)
        button.notify_touch()
        button.notify_touch(release=True)

        self.assertEqual(0, self._short_count)
        self.assertEqual(0, self._long_count)

    def test_longPress_buttonWithShortPressListenerOnly_noTrigger(self):
        scheduler = Scheduler()
        button = Button(scheduler)
        self._long_count = 0
        self._short_count = 0

        def inc_short_count():
            self._short_count += 1

        button.set_short_press(inc_short_count)
        button.set_long_press(None)
        button.notify_touch()
        scheduler.idle(override_time=time.monotonic() + 1)
        button.notify_touch(release=True)

        self.assertEqual(0, self._short_count)
        self.assertEqual(0, self._long_count)


if __name__ == '__main__':
    unittest.main()
