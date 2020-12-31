import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rum_display import DirectDisplay
from rum_display import DisplayWindow


class DirectDisplayTests(unittest.TestCase):
    def setUp(self):

        def push_fn(lines):
            self._pushed = lines

        self._display = (DirectDisplay.Builder()
                         .set_lines(2)
                         .set_line_width(16)
                         .push_with(push_fn)
                         .build())

    def test_initialState_correctDimensions(self):
        self.assertEqual(2, len(self._display))
        self.assertEqual(2, self._display.height())
        self.assertEqual(16, self._display.width())

    def test_initialState_displayPaddedWithSpaces(self):
        self.assertEqual([' ']*16, self._display[0])
        self.assertEqual([' ']*16, self._display[1])

    def test_assignment_displayPaddedWithSpaces(self):
        self._display[0] = '123'
        self.assertEqual(['1', '2', '3'] + [' ']*13, self._display[0])
        self.assertEqual([' ']*16, self._display[1])

    def test_subassignment_portionOfDisplayUpdated(self):
        self._display[0][3:5] = '45'
        self.assertEqual('   45           ', ''.join(self._display[0]))
        self.assertEqual([' ']*16, self._display[1])

    def test_repr_displaysStrings(self):
        self.assertEqual(f'{" ":16}\n{" ":16}', repr(self._display))

    def test_push_callsUnderlyingFunction(self):
        self._display[0][3:5] = '45'
        self._display.push()
        self.assertEqual([
            list('   45           '),
            list(' '*16)], self._pushed)


class DisplayWindowTest(unittest.TestCase):
    def setUp(self):

        def push_fn(lines):
            self._pushed = lines

        self._display = (DirectDisplay.Builder()
                         .set_lines(5)
                         .set_line_width(16)
                         .push_with(push_fn)
                         .build())
        self._window = DisplayWindow(
            self._display, line_range=(2, 4), char_range=(5, 10))

        self._window2 = DisplayWindow(
            self._display, char_range=(5, 10))

        self._window3 = DisplayWindow(
            self._display, line_range=(2, 4))

    def test_initialState_correctDimensions(self):
        self.assertEqual(2, len(self._window))
        self.assertEqual(2, self._window.height())
        self.assertEqual(5, self._window.width())

    def test_underlyingDisplayUpdated_windowUpdated(self):
        self._display[0] = '****************'
        self._display[1] = '****************'
        self._display[2] = '0123456789abcdef'
        self._display[3] = 'ABCDEFGHIJKLMNOP'
        self._display[4] = '****************'

        self.assertEqual(list('56789'), self._window[0])
        self.assertEqual(list('FGHIJ'), self._window[1])

    def test_updateWindow_underlyingDisplayAndOtherWindowsUpdated(self):
        self._display[0] = '****************'
        self._display[1] = '****************'
        self._display[2] = '0123456789abcdef'
        self._display[3] = 'ABCDEFGHIJKLMNOP'
        self._display[4] = '****************'

        self._window[0] = ':)'
        self._window[1] = 'helloworld'

        self.assertEqual(list(':)   '), self._window[0])
        self.assertEqual(list('hello'), self._window[1])

        self.assertEqual(list(':)   '), self._window2[2])
        self.assertEqual(list('hello'), self._window2[3])

        self.assertEqual(list('01234:)   abcdef'), self._window3[0])
        self.assertEqual(list('ABCDEhelloKLMNOP'), self._window3[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('01234:)   abcdef'), self._display[2])
        self.assertEqual(list('ABCDEhelloKLMNOP'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

    def test_pushCalled_propagatesToUnderlyingDisplay(self):
        self._display[0] = '****************'
        self._display[1] = '****************'
        self._display[2] = '0123456789abcdef'
        self._display[3] = 'ABCDEFGHIJKLMNOP'
        self._display[4] = '****************'

        self._window[0] = ':)'
        self._window[1] = 'helloworld'
        self._window.push()
        self.assertEqual([
            list('****************'),
            list('****************'),
            list('01234:)   abcdef'),
            list('ABCDEhelloKLMNOP'),
            list('****************')],
            self._pushed)


if __name__ == '__main__':
    unittest.main()
