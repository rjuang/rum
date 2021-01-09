import unittest

from rum import midi
from rum.matchers import data1_eq, status_eq
from rum.midi import MidiMessage
from rum.processor import MidiProcessor, when


class MidiMessageTests(unittest.TestCase):
    def test_message_constructedProperly(self):
        msg = MidiMessage(1, 2, 3)
        self.assertEqual(1, msg.status)
        self.assertEqual(2, msg.data1)
        self.assertEqual(3, msg.data2)
        self.assertEqual(False, msg.handled)

    def test_channel4Status_properlyDecoded(self):
        msg = MidiMessage(0x84, 2, 3)
        self.assertEqual(0x80, msg.get_masked_status())
        self.assertEqual(4, msg.get_channel())

    def test_convertToBytes_equivalentToInputs(self):
        msg = MidiMessage(0x84, 0x85, 0x86)
        self.assertEqual(bytes([0x84, 0x85, 0x86]), bytes(msg))

    def test_markHandled_handledFieldSet(self):
        msg = MidiMessage(0x84, 2, 3)
        msg.mark_handled()
        self.assertTrue(msg.handled)


class MidiProcessorTests(unittest.TestCase):
    def _increment_count(self, msg):
        self._trigger_count += 1

    def setUp(self):
        self._processor = MidiProcessor()
        self._trigger_count = 0
        self._msg = MidiMessage(128, 30, 34)

    def test_noConditionsAdded_processDoesNotCrash(self):
        self._processor.process(self._msg)

    def test_addFailingCondition_processDoesNotTrigger(self):
        self._processor.add(when(status_eq(100))
                            .then(self._increment_count))
        self._processor.process(self._msg)
        self.assertEqual(0, self._trigger_count)

    def test_addFailingAndPassingCondition_processTriggersOnce(self):
        (self._processor
         .add(when(status_eq(100)).then(self._increment_count))
         .add(when(status_eq(128)).then(self._increment_count))
         .process(self._msg))
        self.assertEqual(1, self._trigger_count)

    def test_addMultiplePassingConditions_allTrigger(self):
        (self._processor
         .add(when(data1_eq(30)).then(self._increment_count),
              when(status_eq(128)).then(self._increment_count))
         .process(self._msg))
        self.assertEqual(2, self._trigger_count)

    def test_getEncoderValueMinMax_returnsMinMaxOfOutput(self):
        self.assertEqual(0, midi.get_encoded_value(MidiMessage(0xB0, 0x05, 0)))
        self.assertEqual(1.0, midi.get_encoded_value(
            MidiMessage(0xB0, 0x05, 0x7F)))
        self.assertAlmostEqual(
            50.0,
            midi.get_encoded_value(
                MidiMessage(0xB0, 0x05, 0), range=(50.0, 100.0)),
            places=4)
        self.assertAlmostEqual(
            100.0,
            midi.get_encoded_value(
                MidiMessage(0xB0, 0x05, 0x7F), range=(50.0, 100.0)),
            places=4)

    def test_getDifferentialEncoderValue_returnsDifferentialOutput(self):
        self.assertAlmostEqual(
            2.0 / 127.0,
            midi.get_encoded_value(
                MidiMessage(0xB0, 0x10, 0x02),
                differential=True),
            5)
        self.assertAlmostEqual(
            -2.0 / 127.0,
            midi.get_encoded_value(
                MidiMessage(0xB0, 0x10, 0x42),
                differential=True),
            5)


if __name__ == '__main__':
    unittest.main()
