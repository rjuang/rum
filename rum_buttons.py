""" Houses classes for managing interaction with things that can be pressed.

This file will contain all things related to some form of a button, i.e. things
that can be pressed and released.
"""

import rum_threading


class Button:
    """ Represents a button that can be pressed normally or long pressed.

    A long press event represents the button being pushed down, held down
    for a period of time that exceeds a threshold, followed by being released.

    A normal press event represents the button being pressed and released
    relatively quickly (less than the threshold interval).
    """
    def __init__(self, scheduler: rum_threading.Scheduler,
                 long_press_delay_ms=450):
        self._scheduler = scheduler
        self._long_press_delay_ms = long_press_delay_ms
        self._on_short_press = None
        self._on_long_press = None
        self._long_press_task = None

    def set_short_press(self, listener):
        """ Specify a listener to run when button is pressed.

        :param listener: the listener to handle short press events or None to
        ignore the event.
        """
        self._on_short_press = listener

    def set_long_press(self, listener):
        """ Specify a listener to run when button is long-pressed.

        :param listener: the listener to handle long press events or None to
        ignore the event.
        """
        self._on_long_press = listener

    def dispatch_long_press(self):
        """ Manually trigger a long-press event. """
        if self._on_long_press:
            self._on_long_press()

    def dispatch_short_press(self):
        """ Manually trigger a short-press event. """
        if self._on_short_press:
            self._on_short_press()

    def notify_touch(self, release=False):
        """ Notify button that a touch event has occurred.

        :param release: set to True if the touch event is a release (touch up)
         event, otherwise set to False (default) to indicate the event is a
         touch down event.
        """
        # On touch-down, we schedule a long press event to be executed after
        # the long press interval is reached.
        # On release, we cancel the scheduled long press. Being unable to cancel
        # the long press event means that it was already executed and a long
        # press event happened.
        if not release:
            self._long_press_task = self._scheduler.schedule(
                self.dispatch_long_press, delay_ms=self._long_press_delay_ms)
        elif self._scheduler.cancel(self._long_press_task):
            self.dispatch_short_press()


if __name__ == '__main__':
    import time

    scheduler = rum_threading.Scheduler()
    button = Button(scheduler)
    long_count = 0
    short_count = 0

    def inc_long_count():
        global long_count
        long_count += 1

    def inc_short_count():
        global short_count
        short_count += 1

    # SCENARIO: Button with short and long press event handlers. Short press.
    button.set_short_press(inc_short_count)
    button.set_long_press(inc_long_count)
    button.notify_touch()
    button.notify_touch(release=True)
    # Verify short event should trigger
    assert short_count == 1
    scheduler.idle(override_time=time.monotonic() + 1)
    # Verify long event never triggers
    assert long_count == 0

    # SCENARIO: Button with short and long press event handlers. Long press.
    long_count = 0
    short_count = 0
    button.notify_touch()
    scheduler.idle(override_time=time.monotonic() + 1)
    button.notify_touch(release=True)
    # Verify short event never triggered
    assert short_count == 0
    # Verify long event triggered
    assert long_count == 1

    # SCENARIO: Button with only long press event handler. Short press.
    long_count = 0
    short_count = 0
    button.set_short_press(None)
    button.set_long_press(inc_long_count)
    button.notify_touch()
    button.notify_touch(release=True)
    # Verify short event never triggered
    assert short_count == 0
    # Verify long event never triggered
    assert long_count == 0

    # SCENARIO: Button with only short press event handler. Long press.
    long_count = 0
    short_count = 0
    button.set_short_press(inc_short_count)
    button.set_long_press(None)
    button.notify_touch()
    scheduler.idle(override_time=time.monotonic() + 1)
    button.notify_touch(release=True)
    # Verify short event never triggered
    assert short_count == 0
    # Verify long event never triggered
    assert long_count == 0
