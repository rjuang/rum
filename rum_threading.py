import _heapq
import itertools
import time


class Scheduler:
    """ Allows tasks to be scheduled for execution (or canceled).

    The purpose of this class is to provide a way for tasks to be scheduled
    and run in a pollable pattern. The only requirement for a Scheduler to be
    used is for the thread to be called continuously at some interval. The
    granularity of the scheduler will depend on the execution interval.
    """

    def __init__(self, time_fn=None):
        # Holds a list of the entries containing (timestamp, task_fn)
        self._tasks_pq = []
        self._counter = itertools.count()
        if time_fn is None:
            time_fn = time.monotonic
        self._time_fn = time_fn

    def _time_ms(self, input_time):
        """ Return current timestamp in seconds if provided input_time is None.

        :param input_time: value in seconds to use as the current time or None.
        :return: the input time in milliseconds or the current time in
        milliseconds.
        """
        return (input_time if input_time is not None
                else self._time_fn()) * 1000

    def schedule(self, task, delay_ms=0, override_time=None):
        """ Schedule a task to be executed after a delay.

        :param task: function to schedule for execution at a later time.
        :param delay_ms: the amount of time in milliseconds to wait until
        executing the function.
        :param override_time: override the value of the current time in seconds.
         If None (default), the time is retrieved from time.monotonic().
        :return: the entry corresponding to the task. This can be used to cancel
        the scheduled task.
        """
        time_ms = self._time_ms(override_time)
        # Add a monotonic value before the task to avoid any ties since lambda
        # functions are not comparable.
        entry = (time_ms + delay_ms, next(self._counter), task)
        _heapq.heappush(self._tasks_pq, entry)
        return entry

    def cancel(self, entry):
        """ Try and cancel a scheduled task that has not been executed.

        :param entry: the entry of the task returned by schedule(...) to cancel
        :return: True if task was successfully canceled. False if the task was
        already executed and could not be canceled.
        """
        try:
            self._tasks_pq.remove(entry)
            return True
        except ValueError:
            # Entry was already removed and executed.
            return False

    def idle(self, override_time=None):
        """ Process an idle loop and processes tasks to be executed.

        :param override_time: override the value of the current time in seconds.
         If None (default), the time is retrieved from time.monotonic().
        """
        time_ms = self._time_ms(override_time)

        while self._tasks_pq:
            entry = _heapq.heappop(self._tasks_pq)
            if entry[0] > time_ms:
                # Entry delay condition not met.
                # Put back on queue and wait until next refresh cycle.
                _heapq.heappush(self._tasks_pq, entry)
                return
            task = entry[-1]
            task()
