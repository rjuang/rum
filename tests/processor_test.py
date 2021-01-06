import unittest


# TODO: Fill in unit tests below

class MidiProcessorTest(unittest.TestCase):
    def test_nothingToProcess_processCalledDoesNothing(self):
        pass

    def test_failingTriggerToProcess_processCalledDoesNothing(self):
        pass

    def test_passingTriggerToProcess_processCalledOnPassingTrigger(self):
        pass

    def test_failedAndPassedTriggersToProcess_onlyPassedTriggers(self):
        pass


class WhenTest(unittest.TestCase):
    def test_whenConditionFails_doesNotTriggerThen(self):
        pass

    def test_whenConditionPasses_triggersThen(self):
        pass


class WhenAllTest(unittest.TestCase):
    def test_whenSingleConditionFails_doesNotTriggerThen(self):
        pass

    def test_whenAllConditionsPass_triggersThen(self):
        pass

    def test_whenNoConditions_triggersThen(self):
        pass


class WhenAllTest(unittest.TestCase):
    def test_whenSingleConditionFails_doesNotTriggerThen(self):
        pass

    def test_whenAllConditionsPass_triggersThen(self):
        pass


class WhenAnyTest(unittest.TestCase):
    def test_whenAllConditionFails_doesNotTriggerThen(self):
        pass

    def test_whenSingleConditionsPass_triggersThen(self):
        pass


class TriggerWhenTest(unittest.TestCase):
    def test_triggerWhenPassAndFailCondition_doesNotCallOnProcess(self):
        pass

    def test_triggerWhenAllPass_callsFunctionOnProcess(self):
        pass

if __name__ == '__main__':
    unittest.main()
