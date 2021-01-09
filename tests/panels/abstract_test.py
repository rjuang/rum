import unittest

from panels.abstract import Panel
from rum import processor, autorefresh
from rum.midi import MidiMessage


_last_panel = None


class TestPanel(Panel):
    """ Test panel implementation. """
    def __init__(self, decorated_arg=None):
        super().__init__()
        self.decorated_arg = decorated_arg
        self.messages = []
        self.init_fns = []
        self.call_values = []
        self.refresh_values = []
        global _last_panel
        _last_panel = self

    def _process_message(self, msg: MidiMessage):
        self.messages.append(msg)

    def _decorate(self, fn):
        self.init_fns.append(fn)

        def decorated_fn(value):
            self.call_values.append(value)
            return fn(value)

        return decorated_fn

    def _refresh(self, flags=0):
        self.refresh_values.append(flags)


class PanelTests(unittest.TestCase):

    def setUp(self):
        # Make sure to clear the singleton states.
        processor.get_processor().clear()
        autorefresh.get_refresh_manager().clear()

        self._panel = TestPanel()
        self._values = []

        @TestPanel(3)
        def on_panel_event(value):
            self._values.append(value)

        global _last_panel
        self._decorated_panel : TestPanel = _last_panel
        self._on_panel_event = on_panel_event

    def test_attachedPanel_processesEvents(self):
        self._panel.attach()
        msg = MidiMessage(123, 456, 789)
        self._panel.process(msg)
        self.assertEqual([msg], self._panel.messages)

    def test_detachedPanel_doesNotProcessEvents(self):
        self._panel.attach()
        self._panel.detach()
        msg = MidiMessage(123, 456, 789)
        self._panel.process(msg)
        self.assertEqual([], self._panel.messages)

    def test_registeredAttachedPanel_processesEvents(self):
        self._panel.register()
        self._panel.attach()
        msg = MidiMessage(123, 456, 789)
        processor.get_processor().process(msg)
        self.assertEqual([msg], self._panel.messages)

    def test_registeredDetachedPanel_doesNotProcessEvents(self):
        self._panel.register()
        self._panel.attach()
        self._panel.detach()
        msg = MidiMessage(123, 456, 789)
        processor.get_processor().process(msg)
        self.assertEqual([], self._panel.messages)

    def test_decoratedPanel_checkSetup(self):
        self.assertEqual(3, self._decorated_panel.decorated_arg)
        self.assertEqual(1, len(self._decorated_panel.init_fns))

    def test_attachedDecoratedPanel_processesEvents(self):
        # Make sure to detach the regular panel so that it's not part of the
        # test
        self._panel.detach()

        msg = MidiMessage(123, 456, 789)
        processor.get_processor().process(msg)
        self.assertEqual([msg], self._decorated_panel.messages)

    def test_detachedDecoratedPanel_doesNotProcessEvents(self):
        self._panel.detach()
        self._decorated_panel.detach()

        msg = MidiMessage(123, 456, 789)
        processor.get_processor().process(msg)
        self.assertEqual([], self._decorated_panel.messages)

    def test_callDecoratedFunction_checkActuallyDecorated(self):
        self._on_panel_event(1)
        # Check decorated function called
        self.assertEqual([1], self._decorated_panel.call_values)
        # Check original function called
        self.assertEqual([1], self._values)

    def test_callingRefreshOnAttachedPanel_triggersRefresh(self):
        self._panel.detach()
        autorefresh.get_refresh_manager().refresh(456)
        self.assertEqual([456], self._decorated_panel.refresh_values)

    def test_callingRefreshOnDettachedPanel_doesNotTriggerRefresh(self):
        self._panel.detach()
        self._decorated_panel.detach()
        autorefresh.get_refresh_manager().refresh(456)
        self.assertEqual([], self._decorated_panel.refresh_values)

    def test_detachAttach_triggersRefreshOnAttach(self):
        self._panel.detach()
        self._decorated_panel.detach()
        self._panel.attach()
        self.assertEqual([autorefresh.FULL_REFRESH], self._panel.refresh_values)


if __name__ == '__main__':
    unittest.main()
