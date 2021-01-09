import unittest

from panels.flstudio.abstract import Panel
from rum import processor
from rum.midi import MidiMessage


class TestPanel(Panel):
    def __init__(self):
        super().__init__()
        self.messages = []
        self.init_fns = []

    def _process_message(self, msg: MidiMessage):
        self.messages.append(msg)

    def _init_decorator(self, fn):
        self.init_fns.append(fn)


class AbstractTests(unittest.TestCase):

    def setUp(self):
        self._panel = TestPanel()

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


if __name__ == '__main__':
    unittest.main()
