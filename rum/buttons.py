""" Houses classes for managing interaction with things that can be pressed.

This file will contain all things related to some form of a button, i.e. things
that can be pressed and released.
"""
from rum import scheduling, states


class Button:
    """ Interface for a button on a midi controller.

    On a MIDI controller, when a physical button is pressed, it generates a
    MIDI event for when the button is pressed down, and another event for when
    the button is released. The occurrence of the press down and release event
    needs to be sent to the button via  on_button_down_event() and
    on_button_up_event().

    The timing of these events can then be interpreted as a regular press or
    a long press. The button implementation is responsible for determining this.
    """

    def set_press_listener(self, listener):
        """ Set the listener that is triggered when a regular press occurs. """
        raise NotImplementedError()

    def set_long_press_listener(self, listener):
        """ Set the listener that is triggered when a long press occurs. """
        raise NotImplementedError()

    def long_press(self):
        """ Manually trigger a long press event. """
        raise NotImplementedError()

    def press(self):
        """ Manually trigger a regular press event. """
        raise NotImplementedError()

    def on_button_down_event(self):
        """ Called when a button down event is detected. """
        raise NotImplementedError()

    def on_button_up_event(self):
        """ Called when a button up event is detected. """
        raise NotImplementedError()


class SimpleButton(Button):
    """ Represents a button that can be pressed normally or long pressed.

    A long press event represents the button being pushed down, held down
    for a period of time that exceeds a threshold, followed by being released.

    A normal press event represents the button being pressed and released
    relatively quickly (less than the threshold interval).

    SimpleButton's job is to classify these two types of events and trigger the
    appropriate listeners.
    """

    def __init__(self, scheduler: scheduling.Scheduler,
                 long_press_delay_ms=450):
        """ Construct a SimpleButton

        :param scheduler:  scheduler to use for scheduling tasks.
        :param long_press_delay_ms: the threshold for which a button must be
        pressed down to be classified as a long press.
        """
        self._scheduler = scheduler
        self._long_press_delay_ms = long_press_delay_ms
        self._on_short_press = None
        self._on_long_press = None
        self._long_press_task = None

    def set_press_listener(self, listener):
        """ Specify a listener to run when button is pressed.

        :param listener: the listener to handle short press events or None to
        ignore the event.
        """
        self._on_short_press = listener

    def set_long_press_listener(self, listener):
        """ Specify a listener to run when button is long-pressed.

        :param listener: the listener to handle long press events or None to
        ignore the event.
        """
        self._on_long_press = listener

    def long_press(self):
        """ Manually trigger a long-press event. """
        if self._on_long_press:
            self._on_long_press()

    def press(self):
        """ Manually trigger a normal press event. """
        if self._on_short_press:
            self._on_short_press()

    def on_button_down_event(self):
        """ Called when a button down event is detected. """
        self._long_press_task = self._scheduler.schedule(
            self.long_press, delay_ms=self._long_press_delay_ms)

    def on_button_up_event(self):
        """ Called when a button up event is detected. """
        if self._scheduler.cancel(self._long_press_task):
            # If long press task is successfully cancelled, then the press
            # is too short and we need to dispatch a short press event.
            self.press()


class ToggleStateButton(Button):
    """ Button that maintains an iterable state that can be toggled.

    When a toggle button is clicked on, it will cycle through the iterable list
    of states. The direction of cycling through the state can be configured (
    default forward direction). When the toggle button is long pressed on, it
    can be configured to toggle through a second state (e.g. for changing modes
    or another state variable).
    """
    def __init__(self,
                 state: states.IterableState,
                 scheduler: scheduling.Scheduler,
                 long_press_state: states.IterableState = None,
                 reverse_direction=False):
        self._button = SimpleButton(scheduler)
        self._state = state
        self._long_press_state = long_press_state
        self._reverse_direction = reverse_direction

        # Short press to iterate through the states
        self._button.set_press_listener(self.press)

        # Long press to trigger a one-time event.
        self._button.set_long_press_listener(self.long_press)

        self._press_listener = None
        self._long_press_listener = None

    def set_press_listener(self, listener):
        self._press_listener = listener

    def set_long_press_listener(self, listener):
        self._long_press_listener = listener

    def long_press(self):
        if self._long_press_state is not None:
            if self._reverse_direction:
                self._long_press_state.toggle_prev()
            else:
                self._long_press_state.toggle_next()
            self._long_press_state.push()

        if self._long_press_listener is not None:
            self._long_press_listener()

    def press(self):
        self._toggle_state()
        if self._press_listener is not None:
            self._press_listener()

    def on_button_down_event(self):
        self._button.on_button_down_event()

    def on_button_up_event(self):
        self._button.on_button_up_event()

    def _toggle_state(self):
        if self._reverse_direction:
            self._state.toggle_prev()
        else:
            self._state.toggle_next()
        # Make sure to publish the event change by pushing out the state change.
        self._state.push()
