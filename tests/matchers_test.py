import sys
import unittest

sys.path.insert(0, '..')
from rum.matchers import midi_eq, status_eq, status_in, status_in_range
from rum.matchers import data1_eq, data1_in, data1_in_range, data2_eq
from rum.matchers import data2_in, data2_in_range, require_all, require_any
from rum.matchers import is_not

from rum.midi import MidiMessage


class MatchersTests(unittest.TestCase):
    def test_matchingMidiEq_matches(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        self.assertEqual(True, midi_eq(0x84, 0x1, 0x2)(msg))

    def test_mismatchingMidiEq_doesNotMatch(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        self.assertEqual(False, midi_eq(0x83, 0x1, 0x2)(msg))
        self.assertEqual(False, midi_eq(0x84, 0x2, 0x2)(msg))
        self.assertEqual(False, midi_eq(0x84, 0x1, 0x3)(msg))

    def test_statusWithChannelBits_matchesStatus(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        self.assertTrue(status_eq(0x84)(msg))
        self.assertFalse(status_eq(0x70)(msg))
        self.assertFalse(status_eq(0x80)(msg))

    def test_statusWithChannelBits_matchesStatusIn(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        self.assertTrue(status_in([0x70, 0x84])(msg))
        self.assertFalse(status_in([0x70, 0x80])(msg))

    def test_statusWithChannelBits_matchesStatusInRange(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        # Test upper bound is included
        self.assertTrue(status_in_range(0x70, 0x84)(msg))
        self.assertTrue(status_in_range(0x70, 0x85)(msg))
        self.assertTrue(status_in_range(0x84, 0x84)(msg))
        self.assertFalse(status_in_range(0x80, 0x79)(msg))
        self.assertFalse(status_in_range(0x78, 0x79)(msg))

        # Test lower bound is included
        self.assertTrue(status_in_range(0x84, 0x85)(msg))
        self.assertFalse(status_in_range(0x85, 0x86)(msg))

    def test_data1_matchesData1(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        self.assertTrue(data1_eq(0x1)(msg))
        self.assertFalse(data1_eq(0x2)(msg))
        self.assertFalse(data1_eq(0x0)(msg))

    def test_data1_matchesData1In(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        self.assertTrue(data1_in([0x01, 0x02])(msg))
        self.assertFalse(data1_in([])(msg))
        self.assertFalse(data1_in([0x0, 0x02])(msg))

    def test_data1_matchesData1InRange(self):
        msg = MidiMessage(0x84, 0x1, 0x2)

        # Test upper bound is included
        self.assertTrue(data1_in_range(0x0, 0x1)(msg))
        self.assertTrue(data1_in_range(0x1, 0x1)(msg))
        self.assertTrue(data1_in_range(0x0, 0x2)(msg))
        self.assertFalse(data1_in_range(0x0, 0x0)(msg))
        self.assertFalse(data1_in_range(0x2, 0x3)(msg))

        # Test lower bound is included
        self.assertTrue(data1_in_range(0x1, 0x2)(msg))
        self.assertFalse(data1_in_range(0x2, 0x3)(msg))

    def test_data2_matchesData1(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        self.assertTrue(data2_eq(0x2)(msg))
        self.assertFalse(data2_eq(0x1)(msg))
        self.assertFalse(data2_eq(0x84)(msg))

    def test_data2_matchesData2In(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        self.assertTrue(data2_in([0x01, 0x02])(msg))
        self.assertFalse(data2_in([])(msg))
        self.assertFalse(data2_in([0x1, 0x84])(msg))

    def test_data2_matchesData1InRange(self):
        msg = MidiMessage(0x84, 0x1, 0x2)

        # Test upper bound is included
        self.assertTrue(data2_in_range(0x0, 0x2)(msg))
        self.assertTrue(data2_in_range(0x2, 0x2)(msg))
        self.assertTrue(data2_in_range(0x0, 0x3)(msg))
        self.assertFalse(data2_in_range(0x0, 0x1)(msg))
        self.assertFalse(data2_in_range(0x3, 0x4)(msg))

        # Test lower bound is included
        self.assertTrue(data2_in_range(0x2, 0x3)(msg))
        self.assertFalse(data2_in_range(0x3, 0x4)(msg))

    def test_allMatchers_requiresAllToMatch(self):
        msg = MidiMessage(0x84, 0x1, 0x2)
        matcher_fn = require_all(
            status_eq(0x84),
            data1_eq(0x01),
            data2_eq(0x02))
        self.assertTrue(matcher_fn(msg))

        matcher_fn = require_all(
            status_eq(0x84),
            data1_eq(0x02),
            data2_eq(0x02))
        self.assertFalse(matcher_fn(msg))

    def test_anyMatchers_requiresAnyToMatch(self):
        msg = MidiMessage(0x80, 0x1, 0x2)
        matcher_fn = any(
            status_eq(0x81),
            status_eq(0x80))
        self.assertTrue(matcher_fn(msg))

        matcher_fn = require_any(
            status_eq(0x70),
            data1_eq(0x12),
            data2_eq(0x22))
        self.assertFalse(matcher_fn(msg))

    def test_notMatcher_flipsMatcherResults(self):
        matcher_fn = is_not(data1_eq(0x3))
        self.assertTrue(matcher_fn(MidiMessage(0x80, 0x1, 0x2)))
        self.assertFalse(matcher_fn(MidiMessage(0x80, 0x3, 0x2)))
