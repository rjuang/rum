import sys
import unittest

sys.path.insert(0, '..')
from rum_threading import Scheduler
from tests.testutils import FakeClock


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self._clock = FakeClock()
        self._scheduler = Scheduler(time_fn=self._clock.time)

    def test_scheduledTasksCanceled_tasksNotExecuted(self):
        self._count = 0

        def inc_count():
            self._count += 1

        entry = self._scheduler.schedule(inc_count)
        self.assertEqual(0, self._count)
        self.assertTrue(self._scheduler.cancel(entry))
        self._clock.advance_by(1)
        self._scheduler.idle()
        self.assertEqual(0, self._count)

    def test_scheduledTasksButInsufficientTimeElapses_tasksNotExecuted(self):
        self._count = 0

        def inc_count():
            self._count += 1
        entry = self._scheduler.schedule(inc_count, delay_ms=5000)
        self._clock.advance_by(1)
        self._scheduler.idle()

        self.assertEqual(0, self._count)
        self.assertTrue(self._scheduler.cancel(entry))

        self._clock.advance_by(100)
        self._scheduler.idle()
        self.assertEqual(0, self._count)

    def test_scheduleTasksWithSufficientDelay_tasksExecute(self):
        self._count = 0

        def inc_count():
            self._count += 1

        # SCENARIO: Tasks scheduled for 5 seconds later. 5 seconds elapses.
        entry = self._scheduler.schedule(inc_count, delay_ms=5000)
        self._clock.advance_by(5)
        self._scheduler.idle()

        self.assertEqual(1, self._count)
        self._clock.advance_by(100)
        self._scheduler.idle()
        self.assertEqual(1, self._count)
        self.assertFalse(self._scheduler.cancel(entry))


if __name__ == '__main__':
    unittest.main()
