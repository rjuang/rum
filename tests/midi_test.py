import sys
import unittest

sys.path.insert(0, '..')
from rum.midi import MidiMessage, Matchers


class MidiMessageTests(unittest.TestCase):
    def test_message_constructedProperly(self):
        msg = MidiMessage(1, 2, 3)
        self.assertEqual(1, msg.status(raw=True))
        self.assertEqual(2, msg.data1())
        self.assertEqual(3, msg.data2())

    def test_channel4Status_properlyDecoded(self):
        msg = MidiMessage(0x84, 2, 3)
        self.assertEqual(0x80, msg.status())
        self.assertEqual(4, msg.channel())

    def test_convertToBytes_equivalentToInputs(self):
        msg = MidiMessage(0x84, 0x85, 0x86)
        self.assertEqual(bytes([0x84, 0x85, 0x86]), bytes(msg))


class MatchersTests(unittest.TestCase):
    def test_statusWithChannelBits_matchesStatus(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        self.assertTrue(Matchers.status_eq(0x80)(msg))
        self.assertFalse(Matchers.status_eq(0x70)(msg))
        self.assertFalse(Matchers.status_eq(0x84)(msg))

    def test_statusWithChannelBits_matchesStatusIn(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        self.assertTrue(Matchers.status_in([0x70, 0x80])(msg))
        self.assertFalse(Matchers.status_in([0x70, 0x84])(msg))

    def test_statusWithChannelBits_matchesStatusInRange(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        # Test upper bound is included
        self.assertTrue(Matchers.status_in_range(0x70, 0x80)(msg))
        self.assertTrue(Matchers.status_in_range(0x70, 0x81)(msg))
        self.assertTrue(Matchers.status_in_range(0x80, 0x80)(msg))
        self.assertFalse(Matchers.status_in_range(0x80, 0x79)(msg))
        self.assertFalse(Matchers.status_in_range(0x78, 0x79)(msg))

        # Test lower bound is included
        self.assertTrue(Matchers.status_in_range(0x80, 0x81)(msg))
        self.assertFalse(Matchers.status_in_range(0x81, 0x82)(msg))

    def test_data1_matchesData1(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        self.assertTrue(Matchers.data1_eq(0x1)(msg))
        self.assertFalse(Matchers.data1_eq(0x2)(msg))
        self.assertFalse(Matchers.data1_eq(0x0)(msg))

    def test_data1_matchesData1In(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        self.assertTrue(Matchers.data1_in([0x01, 0x02])(msg))
        self.assertFalse(Matchers.data1_in([])(msg))
        self.assertFalse(Matchers.data1_in([0x0, 0x02])(msg))

    def test_data1_matchesData1InRange(self):
        msg = MidiMessage(0x84, 0x1, 0x2)

        # Test upper bound is included
        self.assertTrue(Matchers.data1_in_range(0x0, 0x1)(msg))
        self.assertTrue(Matchers.data1_in_range(0x1, 0x1)(msg))
        self.assertTrue(Matchers.data1_in_range(0x0, 0x2)(msg))
        self.assertFalse(Matchers.data1_in_range(0x0, 0x0)(msg))
        self.assertFalse(Matchers.data1_in_range(0x2, 0x3)(msg))

        # Test lower bound is included
        self.assertTrue(Matchers.data1_in_range(0x1, 0x2)(msg))
        self.assertFalse(Matchers.data1_in_range(0x2, 0x3)(msg))

    def test_data2_matchesData1(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        self.assertTrue(Matchers.data2_eq(0x2)(msg))
        self.assertFalse(Matchers.data2_eq(0x1)(msg))
        self.assertFalse(Matchers.data2_eq(0x84)(msg))

    def test_data2_matchesData2In(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        self.assertTrue(Matchers.data2_in([0x01, 0x02])(msg))
        self.assertFalse(Matchers.data2_in([])(msg))
        self.assertFalse(Matchers.data2_in([0x1, 0x84])(msg))

    def test_data2_matchesData1InRange(self):
        msg = MidiMessage(0x84, 0x1, 0x2)

        # Test upper bound is included
        self.assertTrue(Matchers.data2_in_range(0x0, 0x2)(msg))
        self.assertTrue(Matchers.data2_in_range(0x2, 0x2)(msg))
        self.assertTrue(Matchers.data2_in_range(0x0, 0x3)(msg))
        self.assertFalse(Matchers.data2_in_range(0x0, 0x1)(msg))
        self.assertFalse(Matchers.data2_in_range(0x3, 0x4)(msg))

        # Test lower bound is included
        self.assertTrue(Matchers.data2_in_range(0x2, 0x3)(msg))
        self.assertFalse(Matchers.data2_in_range(0x3, 0x4)(msg))

    def test_allMatchers_requiresAllToMatch(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        matcher = Matchers.all(
            Matchers.status_eq(0x80),
            Matchers.data1_eq(0x01),
            Matchers.data2_eq(0x02))
        self.assertTrue(matcher(msg))

        matcher = Matchers.all(
            Matchers.status_eq(0x80),
            Matchers.data1_eq(0x02),
            Matchers.data2_eq(0x02))
        self.assertFalse(matcher(msg))

    def test_anyMatchers_requiresAnyToMatch(self):
        msg = MidiMessage(0x80, 0x1, 0x2)
        matcher = Matchers.any(
            Matchers.status_eq(0x81),
            Matchers.status_eq(0x80))
        self.assertTrue(matcher(msg))

        matcher = Matchers.any(
            Matchers.status_eq(0x70),
            Matchers.data1_eq(0x12),
            Matchers.data2_eq(0x22))
        self.assertFalse(matcher(msg))

    def test_notMatcher_flipsMatcherResults(self):
        matcher = Matchers.is_not(Matchers.data1_eq(0x3))
        self.assertTrue(matcher(MidiMessage(0x80, 0x1, 0x2)))
        self.assertFalse(matcher(MidiMessage(0x80, 0x3, 0x2)))

if __name__ == '__main__':
    unittest.main()
