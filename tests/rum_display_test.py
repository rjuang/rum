import itertools
import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rum_display import DirectDisplay, DisplayWindow, ScrollingDisplay
from rum_threading import Scheduler


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
        self._window = (DisplayWindow.Builder(self._display)
                        .line_range(2, 4)
                        .char_range(5, 10)
                        .build())
        self._window2 = (DisplayWindow.Builder(self._display)
                         .char_range(5, 10)
                         .build())
        self._window3 = (DisplayWindow.Builder(self._display)
                         .line_range(2, 4)
                         .build())

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


class ScrollingDisplayTest(unittest.TestCase):
    def setUp(self):
        self._time_sequence = itertools.count(0.0, 0.0001)
        self._last_timestamp = 0

        def push_fn(lines):
            self._pushed = lines

        def time_fn():
            self._last_timestamp = next(self._time_sequence)
            return self._last_timestamp

        self._scheduler = Scheduler(time_fn=time_fn)
        self._display = (DirectDisplay.Builder()
                         .set_lines(5)
                         .set_line_width(16)
                         .push_with(push_fn)
                         .build())

        window = (DisplayWindow.Builder(self._display)
                  .line_range(2, 4)
                  .char_range(5, 10)
                  .build())

        self._window = ScrollingDisplay(window,
                                        self._scheduler,
                                        scroll_interval_ms=250,
                                        scroll_amount=1,
                                        padding=2)

        self._display[0] = '****************'
        self._display[1] = '****************'
        self._display[2] = '*****     ******'
        self._display[3] = '*****     ******'
        self._display[4] = '****************'

    def test_dimensions_matchUnderlyingWindow(self):
        self.assertEqual(2, self._window.height())
        self.assertEqual(5, self._window.width())
        self.assertEqual(2, len(self._window))

    def test_setLongLines_contentContainsFullLines(self):
        self._window[0] = 'hello world'
        self._window[0] += '!'
        self._window[1] = 'this is a test'

        self.assertEqual('hello world!', self._window[0])
        self.assertEqual('this is a test', self._window[1])

    def test_setShortLines_contentContainsFullLines(self):
        self._window[0] = 'hello'
        self._window[1] = 'world'

        self.assertEqual('hello', self._window[0])
        self.assertEqual('world', self._window[1])

    def test_allShortLines_noScrolling(self):
        self._window[0] = 'hello'
        self._window[1] = 'world'
        self._scheduler.idle(override_time=1)

        self.assertEqual('hello', self._window[0])
        self.assertEqual('world', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****hello******'), self._display[2])
        self.assertEqual(list('*****world******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

    def test_allLongLines_bothScrolling(self):
        self._window[0] = 'hello!!'
        self._window[1] = 'world!'

        # Iteration 1
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)

        self.assertEqual('hello!!', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****ello!******'), self._display[2])
        self.assertEqual(list('*****orld!******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 2
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)

        self.assertEqual('hello!!', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****llo!!******'), self._display[2])
        self.assertEqual(list('*****rld! ******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 3
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)

        self.assertEqual('hello!!', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****lo!! ******'), self._display[2])
        self.assertEqual(list('*****ld!  ******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 4
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)

        self.assertEqual('hello!!', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****o!!  ******'), self._display[2])
        self.assertEqual(list('*****d!  w******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 5
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)

        self.assertEqual('hello!!', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****!!  h******'), self._display[2])
        self.assertEqual(list('*****!  wo******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 6
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)
        self.assertEqual(list('*****!  he******'), self._display[2])
        self.assertEqual(list('*****  wor******'), self._display[3])

        # Iteration 7
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)
        self.assertEqual(list('*****  hel******'), self._display[2])
        self.assertEqual(list('***** worl******'), self._display[3])

        # Iteration 8
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)
        self.assertEqual(list('***** hell******'), self._display[2])
        self.assertEqual(list('*****world******'), self._display[3])

        # Iteration 9
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)
        self.assertEqual(list('*****hello******'), self._display[2])
        self.assertEqual(list('*****orld!******'), self._display[3])

    def test_bothShortAndLongLines_onlyLongScrolling(self):
        self._window[0] = 'hello'
        self._window[1] = 'world!'

        # Iteration 1
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)

        self.assertEqual('hello', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****hello******'), self._display[2])
        self.assertEqual(list('*****orld!******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 2
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)

        self.assertEqual('hello', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****hello******'), self._display[2])
        self.assertEqual(list('*****rld! ******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 3
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)
        self.assertEqual(list('*****hello******'), self._display[2])
        self.assertEqual(list('*****ld!  ******'), self._display[3])

        # Iteration 4
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)
        self.assertEqual(list('*****d!  w******'), self._display[3])

        # Iteration 5
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)
        self.assertEqual(list('*****!  wo******'), self._display[3])

        # Iteration 6
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)
        self.assertEqual(list('*****  wor******'), self._display[3])

        # Iteration 7
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)
        self.assertEqual(list('***** worl******'), self._display[3])

        # Iteration 8
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)
        self.assertEqual(list('*****world******'), self._display[3])

    def test_updateTextWhileScrolling_startsBackAt0(self):
        self._window[0] = 'hello!!'
        self._window[1] = 'world!'

        # Iteration 1
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)

        self.assertEqual('hello!!', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****ello!******'), self._display[2])
        self.assertEqual(list('*****orld!******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 2
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)

        self.assertEqual('hello!!', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****llo!!******'), self._display[2])
        self.assertEqual(list('*****rld! ******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Insert text
        self._window[0] = 'hello!!'

        # Iteration 3
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****hello******'), self._display[2])
        self.assertEqual(list('*****ld!  ******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 4
        self._scheduler.idle(override_time=self._last_timestamp + 0.250)

        self.assertEqual('hello!!', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****ello!******'), self._display[2])
        self.assertEqual(list('*****d!  w******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])


if __name__ == '__main__':
    unittest.main()
