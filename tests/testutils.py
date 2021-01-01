""" Convenience classes and functions to simplify writing tests. """
import itertools


class FakeClock:
    """ Fake clock that returns an incrementing value as the time. """

    def __init__(self, start=0.0, step=0.0001):
        """ Construct a fake clock with the given and increments by step.

        :param start: the starting time value to return for the first call.
        :param step: the time increment that is returned for each susequent
        calls.
        """
        self._start = start
        self._step = step
        self._counter = itertools.count(0, 1)
        self._last_timestamp = start

    def time(self):
        """ Fetch the current time """
        self._last_timestamp = self._start + next(self._counter) * self._step
        return self._last_timestamp

    def advance_by(self, delta):
        self._start += delta

    def last_reported(self):
        """ Returns the last timestamp fetched. """
        return self._last_timestamp
