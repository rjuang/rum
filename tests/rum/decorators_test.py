import unittest

from rum import processor, registry
from rum.decorators import trigger_when, button, encoder, slider
from rum.matchers import status_eq, data1_eq, midi_has
from rum.midi import MidiMessage


class TriggerWhenTests(unittest.TestCase):
    def test_triggerWhenPassAndFailCondition_doesNotCallOnProcess(self):
        self._received = []

        @trigger_when(status_eq(128), data1_eq(1))
        def dispatch(m):
            self._received.append(m)

        m = MidiMessage(128, 0, 2)
        processor.get_processor().process(m)
        self.assertEqual([], self._received)

    def test_triggerWhenAllPass_callsFunctionOnProcess(self):
        self._received = []

        @trigger_when(status_eq(128), data1_eq(1))
        def dispatch(m):
            self._received.append(m)

        m = MidiMessage(128, 1, 2)
        processor.get_processor().process(m)
        self.assertEqual([m], self._received)


class ButtonTests(unittest.TestCase):
    def setUp(self):
        self._values = []

        @button('test_btn',
                midi_has(status=0x90, data1=0x30),
                midi_has(status=0x80, data1=0x30))
        def on_button(m: MidiMessage, is_pressed):
            self._values.append(is_pressed)

        self._on_button = on_button

    def test_unmatchedInput_doesNotTriggerButton(self):
        processor.get_processor().process(MidiMessage(0xb0, 0x30, 0x01))
        self.assertEqual([], self._values)
        self.assertFalse(registry.button_down['test_btn'])

    def test_matchedOnDataInput_triggersButtonAndSetsButtonRegistry(self):
        processor.get_processor().process(MidiMessage(0x90, 0x30, 0x01))
        self.assertEqual([True], self._values)
        self.assertTrue(registry.button_down['test_btn'])

    def test_matchedOnOffDataInput_triggersButtonOnOffUpdatesRegistry(self):
        processor.get_processor().process(MidiMessage(0x90, 0x30, 0x01))
        processor.get_processor().process(MidiMessage(0x80, 0x30, 0x02))
        self.assertEqual([True, False], self._values)
        self.assertFalse(registry.button_down['test_btn'])


class EncoderTests(unittest.TestCase):
    def setUp(self):
        self._values = []
        registry.encoders.clear()

        @encoder('test_regular_enc', midi_has(status=0x90, data1=0x30))
        def on_regular_enc(m: MidiMessage, value):
            self._values.append(value)
        self.on_regular_enc =  on_regular_enc

        @encoder('test_infinite_enc', midi_has(status=0x90, data1=0x32),
                 infinite=True)
        def on_infinite_enc(m: MidiMessage, value):
            self._values.append(value)
        self.on_differential_enc = on_infinite_enc

    def test_unmatchedInput_doesNotTriggerEncoder(self):
        processor.get_processor().process(MidiMessage(0x90, 0x29, 0x2))
        self.assertEqual([], self._values)
        self.assertEqual(0.0, registry.encoders['test_regular_enc'])
        self.assertEqual(0.0, registry.encoders['test_infinite_enc'])

    def test_matchedDataInput_triggersAndSetsRegistry(self):
        processor.get_processor().process(MidiMessage(0x90, 0x30, 0x42))
        self.assertEqual([0x42/127.0], self._values)
        self.assertEqual(0x42/127.0, registry.encoders['test_regular_enc'])
        self.assertEqual(0.0, registry.encoders['test_infinite_enc'])

    def test_matchedDataInputForInfiniteEnc_triggersAndSetsRegistry(self):
        processor.get_processor().process(MidiMessage(0x90, 0x32, 0x42))
        self.assertEqual([-2.0/127.0], self._values)
        self.assertEqual(0.0/127.0, registry.encoders['test_regular_enc'])
        self.assertEqual(-2.0/127.0, registry.encoders['test_infinite_enc'])


class SlidersTests(unittest.TestCase):
    def setUp(self):
        self._values = []
        registry.sliders.clear()

        @slider('test_slider', midi_has(status=0x90, data1=0x30))
        def on_regular_enc(m: MidiMessage, value):
            self._values.append(value)
        self.on_regular_enc =  on_regular_enc

    def test_unmatchedInput_doesNotTriggerSlider(self):
        processor.get_processor().process(MidiMessage(0x90, 0x29, 0x2))
        self.assertEqual([], self._values)
        self.assertEqual(0.0, registry.sliders['test_slider'])

    def test_matchedDataInput_triggersAndSetsRegistry(self):
        processor.get_processor().process(MidiMessage(0x90, 0x30, 0x42))
        self.assertEqual([0x42/127.0], self._values)
        self.assertEqual(0x42/127.0, registry.sliders['test_slider'])


if __name__ == '__main__':
    unittest.main()
