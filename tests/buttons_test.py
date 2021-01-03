import sys
import unittest


sys.path.insert(0, '..')
from rum.buttons import SimpleButton, ToggleStateButton
from rum.states import IterableState
from rum.scheduling import Scheduler
from tests.testutils import FakeClock


class SimpleButtonTests(unittest.TestCase):
    def setUp(self):
        self._clock = FakeClock()
        self._scheduler = Scheduler(time_fn=self._clock.time)
        self._button = SimpleButton(self._scheduler)

        self._long_count = 0
        self._short_count = 0

        def inc_long_count():
            self._long_count += 1

        def inc_short_count():
            self._short_count += 1

        self._button.set_press_listener(inc_short_count)
        self._button.set_long_press_listener(inc_long_count)

    def test_shortPress_buttonWithListeners_listenersTrigger(self):
        self._button.on_button_down_event()
        self._button.on_button_up_event()

        self.assertEqual(1, self._short_count)
        self._clock.advance(1)
        self._scheduler.idle()
        self.assertEqual(0, self._long_count)

    def test_longPress_buttonWithListeners_listenersTrigger(self):
        self._long_count = 0
        self._short_count = 0

        self._button.on_button_down_event()
        self._clock.advance(1)
        self._scheduler.idle()
        self._button.on_button_up_event()

        self.assertEqual(0, self._short_count)
        self.assertEqual(1, self._long_count)

    def test_shortPress_buttonWithLongPressListenerOnly_noTrigger(self):
        self._button.set_press_listener(None)
        self._button.on_button_down_event()
        self._button.on_button_up_event()

        self.assertEqual(0, self._short_count)
        self.assertEqual(0, self._long_count)

    def test_longPress_buttonWithShortPressListenerOnly_noTrigger(self):
        self._button.set_long_press_listener(None)
        self._button.on_button_down_event()
        self._clock.advance(1)
        self._scheduler.idle()
        self._button.on_button_up_event()

        self.assertEqual(0, self._short_count)
        self.assertEqual(0, self._long_count)


class ToggleStateButtonTests(unittest.TestCase):
    def setUp(self):
        self._pushed_state = ''
        self._clock = FakeClock()
        def push_fn(x): self._pushed_state = x
        self._state = (IterableState.Builder('rec')
                       .add_states(['OFF', 'ON'])
                       .default_to('OFF')
                       .push_with(push_fn)
                       .build())
        self._long_press_state = (IterableState.Builder('user')
                                  .add_states(['NOT_FLASHING', 'FLASHING'])
                                  .default_to('NOT_FLASHING')
                                  .push_with(push_fn)
                                  .build())
        self._scheduler = Scheduler(time_fn=self._clock.time)
        self._button = ToggleStateButton(
            self._state,
            self._scheduler,
            long_press_state=self._long_press_state,
            reverse_direction=False)

        self._press_count = 0
        self._long_press_count = 0

        def press_listener(): self._press_count += 1
        def long_press_listener(): self._long_press_count += 1

        self._button.set_press_listener(press_listener)
        self._button.set_long_press_listener(long_press_listener)

    def test_buttonWithListeners_pressButtonTogglesState(self):
        self.assertEqual('OFF', self._state.get())
        self._button.on_button_down_event()
        self._button.on_button_up_event()

        self.assertEqual('ON', self._state.get())
        self.assertEqual('NOT_FLASHING', self._long_press_state.get())
        self.assertEqual(1, self._press_count)
        self.assertEqual(0, self._long_press_count)

        self._button.on_button_down_event()
        self._button.on_button_up_event()
        self.assertEqual('OFF', self._state.get())
        self.assertEqual(2, self._press_count)
        self.assertEqual(0, self._long_press_count)
        self.assertEqual('NOT_FLASHING', self._long_press_state.get())

    def test_buttonWithListeners_pressButtonTogglesState(self):
        self._button.set_press_listener(None)
        self.assertEqual('OFF', self._state.get())
        self._button.on_button_down_event()
        self._button.on_button_up_event()

        self.assertEqual('ON', self._state.get())
        self.assertEqual('NOT_FLASHING', self._long_press_state.get())
        self.assertEqual(0, self._press_count)
        self.assertEqual(0, self._long_press_count)

        self._button.on_button_down_event()
        self._button.on_button_up_event()
        self.assertEqual('OFF', self._state.get())
        self.assertEqual(0, self._press_count)
        self.assertEqual(0, self._long_press_count)
        self.assertEqual('NOT_FLASHING', self._long_press_state.get())

    def test_buttonWithListeners_pressButtonTogglesState(self):
        self.assertEqual('OFF', self._state.get())
        self._button.on_button_down_event()
        self._clock.advance(0.450)
        self._scheduler.idle()
        self._button.on_button_up_event()

        # Long press, trigger long press state change
        self.assertEqual('OFF', self._state.get())
        self.assertEqual('FLASHING', self._long_press_state.get())
        self.assertEqual(0, self._press_count)
        self.assertEqual(1, self._long_press_count)

        # Regular press, trigger short press state change
        self._button.on_button_down_event()
        self._button.on_button_up_event()
        self.assertEqual('ON', self._state.get())
        self.assertEqual('FLASHING', self._long_press_state.get())
        self.assertEqual(1, self._press_count)
        self.assertEqual(1, self._long_press_count)


if __name__ == '__main__':
    unittest.main()
