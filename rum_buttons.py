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


class ToggleButton:
    """ Buttons that maintain an On/Off or True/False state. """
    def __init__(self, scheduler: rum_threading.Scheduler, state=False):
        self._button = Button(scheduler)
        # Treat both short/long release as a regular press to toggle.
        self._button.set_short_press(self.toggle)
        self._button.set_long_press(self.toggle)

        self._listener = None
        self._state = state

    def toggle(self):
        """ Manually toggle the state of the button.

        Note: This will also trigger the listener for the updated state.
        """
        self._state = not self._state
        self._dispatch_state_listener()

    def get(self):
        """ Return the current state of the button. """
        return self._state

    def set(self, new_state: bool):
        """ Manually set the state of the button.

        Note: This will only trigger the listener if the state changed
        """
        dispatch = new_state != self._state
        self._state = new_state
        if dispatch:
            self._dispatch_state_listener()

    def set_change_listener(self, listener):
        """ Set the listener that is triggered when the button state changes.

        :param listener:  the listener to trigger on button state changes or
        None to drop.
        """
        self._listener = listener

    def notify_touch(self, release=False):
        """ Notify the toggle button that a touch event has occurred.

        :param release:  set to True to indicate that a touch up event has
        occurred. Leave False (default) to indicate that a touch down event has
        occurred.
        """
        self._button.notify_touch(release)

    def _dispatch_state_listener(self):
        if self._listener:
            self._listener()
