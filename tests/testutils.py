""" Convenience classes and functions to simplify writing tests. """
import itertools


class FakeClock:
    """ Fake clock that with a time value that can be manually controlled. """

    def __init__(self, start=0.0, step=0.0001):
        """ Construct a clock with the given start and default step increment.

        :param start: the starting time value to return for the first call.
        :param step: the default time increment to advance the clock by if
        advance is called with no arguments.
        """
        self._start = start
        self._step = step
        self._counter = itertools.count(0, 1)
        self._last_timestamp = start

    def time(self):
        """ Fetch the current time """
        return self._last_timestamp

    def advance(self, amount=None):
        """ Advance the current time.

        The time is advanced by the default step or the provided amount if one
        is provided.
        :param amount: optional amount to advance the time b
        :return the updated time.
        """
        if amount is not None:
            self._start += amount
            self._last_timestamp += amount
        else:
            self._last_timestamp = self._start + next(self._counter) * self._step
        return self._last_timestamp
