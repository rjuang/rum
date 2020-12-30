import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rum_state import IterableState

class IterableStateTests(unittest.TestCase):
    def test_initialState_hasCorrectName(self):
        state = (IterableState.Builder('testProp')
                 .add_states([1, 2, 3])
                 .build())
        self.assertEqual('testProp', state.name())

    def test_initialStateWithDefaultUnset_hasCorrectStartingValue(self):
        state = (IterableState.Builder('testProp')
                 .add_states([1, 2, 3])
                 .build())
        self.assertEqual(1, state.get())

    def test_initiaStateWithDefaultSet_hasCorrectStartingValue(self):
        state = (IterableState.Builder('testProp')
                 .add_states([1, 2, 3])
                 .default_to(2)
                 .build())
        self.assertEqual(2, state.get())

    def test_toggleNext_goesToCorrectNextValue(self):
        state = (IterableState.Builder('testProp')
                 .add_states([1, 2, 3])
                 .default_to(2)
                 .build())
        self.assertEqual(2, state.get())

        self.assertEqual(3, state.toggle_next())
        self.assertEqual(3, state.get())

        self.assertEqual(1, state.toggle_next())
        self.assertEqual(1, state.get())

        self.assertEqual(2, state.toggle_next())
        self.assertEqual(2, state.get())

    def test_togglePrev_goesToCorrectPreviousValue(self):
        state = (IterableState.Builder('testProp')
                 .add_states([1, 2, 3])
                 .default_to(2)
                 .build())
        self.assertEqual(2, state.get())

        self.assertEqual(1, state.toggle_prev())
        self.assertEqual(1, state.get())

        self.assertEqual(3, state.toggle_prev())
        self.assertEqual(3, state.get())

        self.assertEqual(2, state.toggle_prev())
        self.assertEqual(2, state.get())

    def test_push_correctlyPassesTheCurrentValue(self):
        self._value = -1

        def push_fn(x):
            self._value = x

        state = (IterableState.Builder('testProp')
                 .add_states([1, 2, 3])
                 .default_to(2)
                 .push_with(push_fn)
                 .build())

        state.push()
        self.assertEqual(2, self._value)

    def test_toggleState_doesNotAutoPush(self):
        self._value = -1

        def push_fn(x):
            self._value = x

        state = (IterableState.Builder('testProp')
                 .add_states([1, 2, 3])
                 .default_to(2)
                 .push_with(push_fn)
                 .build())

        state.push()
        state.toggle_prev()  # 1
        state.toggle_next()  # 2
        state.toggle_next()  # 3

        self.assertEqual(2, self._value)
        state.push()
        self.assertEqual(3, self._value)

    def test_pull_correctlyUpdatesTheState(self):
        self._value = 3

        def pull_fn():
            return self._value

        state = (IterableState.Builder('testProp')
                 .add_states([1, 2, 3])
                 .default_to(2)
                 .pull_with(pull_fn)
                 .build())

        self.assertTrue(state.pull())
        self.assertEqual(3, state.get())

        self._value = 2
        self.assertTrue(state.pull())
        self.assertEqual(2, state.get())

    def test_pull_returnsFalseWhenNoUpdates(self):
        self._value = 3

        def pull_fn():
            return self._value

        state = (IterableState.Builder('testProp')
                 .add_states([1, 2, 3])
                 .default_to(2)
                 .pull_with(pull_fn)
                 .build())

        state.pull()
        self.assertFalse(state.pull())
        self.assertEqual(3, state.get())

    def test_pullAndPush_correctlyPullsUpdatedValueAndPushes(self):
        self._value = 3
        self._push_value = 0

        def pull_fn():
            return self._value

        def push_fn(x):
            self._push_value = x

        state = (IterableState.Builder('testProp')
                 .add_states([1, 2, 3])
                 .default_to(2)
                 .pull_with(pull_fn)
                 .push_with(push_fn)
                 .build())

        self.assertTrue(state.pull())
        state.push()

        self.assertTrue(3, self._value)
        self.assertTrue(3, self._push_value)
        self.assertEqual(3, state.get())


if __name__ == '__main__':
    unittest.main()
