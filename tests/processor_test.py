import sys
import unittest

sys.path.insert(0, '..')

from rum import processor
from rum.matchers import status_eq, data1_eq
from rum.midi import MidiMessage
from rum.processor import MidiProcessor, When, WhenAll, WhenAny, trigger_when


class MidiProcessorTest(unittest.TestCase):
    def setUp(self):
        self._processor = MidiProcessor()

    def test_nothingToProcess_processCalledDoesNothing(self):
        self._processor.process(MidiMessage(0x128, 0x28, 0x30))
        # Passes as long as this doesn't crash

    def test_processFunctionAdded_nothingCalledIfProcessNotCalled(self):
        self._cnt = 0

        def process(_):
            self._cnt += 1

        self._processor.add(process)
        self.assertEqual(0, self._cnt)

    def test_processFunctionAdded_fnCalledWhenProcessCalled(self):
        self._cnt = 0

        def process(_):
            self._cnt += 1

        self._processor.add(process)
        self._processor.process(MidiMessage(128, 3, 4))
        self.assertEqual(1, self._cnt)

    def test_processFunctionAdded_multipleProcessCall(self):
        self._cnt = 0

        def process(_):
            self._cnt += 1

        self._processor.add(process)
        self._processor.process(MidiMessage(128, 3, 4))
        self._processor.process(MidiMessage(128, 3, 5))
        self._processor.process(MidiMessage(128, 3, 4))
        self.assertEqual(3, self._cnt)


class WhenTest(unittest.TestCase):
    def test_whenConditionFails_doesNotTriggerThen(self):
        self._cnt = 0

        def increment_cnt(_):
            self._cnt += 1

        process = When(status_eq(34)).then(increment_cnt)
        process(MidiMessage(35, 1, 1))
        self.assertEqual(0, self._cnt)

    def test_whenConditionPasses_triggersThen(self):
        self._received = []

        def dispatch(m):
            self._received.append(m)

        process = When(status_eq(34)).then(dispatch)
        m = MidiMessage(34, 1, 1)
        process(m)
        self.assertEqual([m], self._received)


class WhenAllTest(unittest.TestCase):
    def test_whenSingleConditionFails_doesNotTriggerThen(self):
        self._received = []

        def dispatch(m):
            self._received.append(m)

        process = WhenAll(status_eq(33), data1_eq(0)).then(dispatch)
        m = MidiMessage(33, 1, 1)
        process(m)
        self.assertEqual([], self._received)

    def test_whenAllConditionsPass_triggersThen(self):
        self._received = []

        def dispatch(m):
            self._received.append(m)

        process = WhenAll(status_eq(34), data1_eq(1)).then(dispatch)
        m = MidiMessage(34, 1, 1)
        process(m)
        self.assertEqual([m], self._received)

    def test_whenNoConditions_triggersThen(self):
        self._received = []

        def dispatch(m):
            self._received.append(m)

        process = WhenAll(status_eq(34), data1_eq(2)).then(dispatch)
        m = MidiMessage(33, 1, 1)
        process(m)
        self.assertEqual([], self._received)


class WhenAnyTest(unittest.TestCase):
    def test_whenAllConditionFails_doesNotTriggerThen(self):
        self._received = []

        def dispatch(m):
            self._received.append(m)

        process = WhenAny(status_eq(34), data1_eq(1)).then(dispatch)
        m = MidiMessage(33, 0, 1)
        process(m)
        self.assertEqual([], self._received)

    def test_whenSingleConditionsPass_triggersThen(self):
        self._received = []

        def dispatch(m):
            self._received.append(m)

        process = WhenAny(status_eq(34), data1_eq(1)).then(dispatch)
        m = MidiMessage(33, 1, 1)
        process(m)
        self.assertEqual([m], self._received)


class TriggerWhenTest(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
