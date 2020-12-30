import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rum_threading import Scheduler


class SchedulerTests(unittest.TestCase):
    def test_scheduledTasksCanceled_tasksNotExecuted(self):
        scheduler = Scheduler()
        self._count = 0

        def inc_count():
            self._count += 1

        entry = scheduler.schedule(inc_count, override_time=0)
        self.assertEqual(0, self._count)
        self.assertTrue(scheduler.cancel(entry))

        scheduler.idle(override_time=100)
        self.assertEqual(0, self._count)

    def test_scheduledTasksButInsufficientTimeElapses_tasksNotExecuted(self):
        scheduler = Scheduler()
        self._count = 0

        def inc_count():
            self._count += 1

        entry = scheduler.schedule(inc_count, delay_ms=5000, override_time=0)
        scheduler.idle(override_time=1)

        self.assertEqual(0, self._count)
        self.assertTrue(scheduler.cancel(entry))

        scheduler.idle(override_time=100)
        self.assertEqual(0, self._count)

    def test_scheduleTasksWithSufficientDelay_tasksExecute(self):
        scheduler = Scheduler()
        self._count = 0

        def inc_count():
            self._count += 1

        # SCENARIO: Tasks scheduled for 5 seconds later. 5 seconds elapses.
        entry = scheduler.schedule(inc_count, delay_ms=5000, override_time=0)
        scheduler.idle(override_time=5)

        self.assertEqual(1, self._count)
        scheduler.idle(override_time=100)
        self.assertEqual(1, self._count)
        self.assertFalse(scheduler.cancel(entry))


if __name__ == '__main__':
    unittest.main()
