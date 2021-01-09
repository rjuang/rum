import unittest

from rum.displays import DirectDisplay, DisplayWindow, ScrollingDisplay, \
    PagedDisplay
from rum.scheduling import Scheduler
from tests.testutils import FakeClock


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
        self._clock = FakeClock()

        def push_fn(lines):
            self._pushed = lines

        self._scheduler = Scheduler(time_fn=self._clock.time)
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
        self._clock.advance(0.250)
        self._scheduler.idle()

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
        self._clock.advance(0.250)
        self._scheduler.idle()

        self.assertEqual('hello!!', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****ello!******'), self._display[2])
        self.assertEqual(list('*****orld!******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 2
        self._clock.advance(0.250)
        self._scheduler.idle()

        self.assertEqual('hello!!', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****llo!!******'), self._display[2])
        self.assertEqual(list('*****rld! ******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 3
        self._clock.advance(0.250)
        self._scheduler.idle()

        self.assertEqual('hello!!', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****lo!! ******'), self._display[2])
        self.assertEqual(list('*****ld!  ******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 4
        self._clock.advance(0.250)
        self._scheduler.idle()

        self.assertEqual('hello!!', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****o!!  ******'), self._display[2])
        self.assertEqual(list('*****d!  w******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 5
        self._clock.advance(0.250)
        self._scheduler.idle()

        self.assertEqual('hello!!', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****!!  h******'), self._display[2])
        self.assertEqual(list('*****!  wo******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 6
        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual(list('*****!  he******'), self._display[2])
        self.assertEqual(list('*****  wor******'), self._display[3])

        # Iteration 7
        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual(list('*****  hel******'), self._display[2])
        self.assertEqual(list('***** worl******'), self._display[3])

        # Iteration 8
        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual(list('***** hell******'), self._display[2])
        self.assertEqual(list('*****world******'), self._display[3])

        # Iteration 9
        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual(list('*****hello******'), self._display[2])
        self.assertEqual(list('*****orld!******'), self._display[3])

    def test_bothShortAndLongLines_onlyLongScrolling(self):
        self._window[0] = 'hello'
        self._window[1] = 'world!'

        # Iteration 1
        self._clock.advance(0.250)
        self._scheduler.idle()

        self.assertEqual('hello', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****hello******'), self._display[2])
        self.assertEqual(list('*****orld!******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 2
        self._clock.advance(0.250)
        self._scheduler.idle()

        self.assertEqual('hello', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****hello******'), self._display[2])
        self.assertEqual(list('*****rld! ******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 3
        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual(list('*****hello******'), self._display[2])
        self.assertEqual(list('*****ld!  ******'), self._display[3])

        # Iteration 4
        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual(list('*****d!  w******'), self._display[3])

        # Iteration 5
        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual(list('*****!  wo******'), self._display[3])

        # Iteration 6
        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual(list('*****  wor******'), self._display[3])

        # Iteration 7
        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual(list('***** worl******'), self._display[3])

        # Iteration 8
        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual(list('*****world******'), self._display[3])

    def test_updateTextWhileScrolling_startsBackAt0(self):
        self._window[0] = 'hello!!'
        self._window[1] = 'world!'

        # Iteration 1
        self._clock.advance(0.250)
        self._scheduler.idle()

        self.assertEqual('hello!!', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****ello!******'), self._display[2])
        self.assertEqual(list('*****orld!******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 2
        self._clock.advance(0.250)
        self._scheduler.idle()

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
        self._clock.advance(0.250)
        self._scheduler.idle()

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****hello******'), self._display[2])
        self.assertEqual(list('*****ld!  ******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])

        # Iteration 4
        self._clock.advance(0.250)
        self._scheduler.idle()

        self.assertEqual('hello!!', self._window[0])
        self.assertEqual('world!', self._window[1])

        self.assertEqual(list('****************'), self._display[0])
        self.assertEqual(list('****************'), self._display[1])
        self.assertEqual(list('*****ello!******'), self._display[2])
        self.assertEqual(list('*****d!  w******'), self._display[3])
        self.assertEqual(list('****************'), self._display[4])


class PagedDisplayTests(unittest.TestCase):
    def setUp(self):
        self._clock = FakeClock()
        self._pushed = None

        def push_fn(lines):
            self._pushed = [line[:] for line in lines]

        self._scheduler = Scheduler(time_fn=self._clock.time)
        self._display = (DirectDisplay.Builder()
                         .set_lines(2)
                         .set_line_width(16)
                         .push_with(push_fn)
                         .build())
        self._paged_display = PagedDisplay(self._display, self._scheduler)
        self._display[0] = 'Hello'
        self._display[1] = 'World'

    def test_pagedDisplay_matchesUnderlyingDimensions(self):
        self.assertEqual(2, len(self._paged_display))
        self.assertEqual(16, self._paged_display.width())

    def test_setInactivePage_doesNotImpactCurrentDisplay(self):
        self._paged_display.page('page1')[0] = 'goodbye'
        self._paged_display.page('page1')[1] = 'unittest'
        self.assertEqual(list('Hello           '), self._display[0])
        self.assertEqual(list('World           '), self._display[1])
        self.assertEqual(['goodbye', 'unittest'],
                         self._paged_display.page('page1'))
        self.assertEqual(None, self._pushed)

    def test_setActivePage_alsoUpdatesDisplay(self):
        self._paged_display.page('main')[0] = 'main'
        self._paged_display.page('main')[1] = 'page'
        self._paged_display.set_active_page('main')
        self.assertEqual(list('main            '), self._display[0])
        self.assertEqual(list('page            '), self._display[1])
        self.assertEqual([list('main            '),
                          list('page            ')],
                         self._pushed)

    def test_directlyChangeActivePage_alsoUpdatesActiveKey(self):
        self._paged_display.page('main')[0] = 'main'
        self._paged_display.page('main')[1] = 'page'
        self._paged_display.set_active_page('main')
        self._paged_display[0] = 'changed'
        self._paged_display[1] = 'text'
        self.assertEqual(list('changed         '), self._display[0])
        self.assertEqual(list('text            '), self._display[1])
        self.assertEqual(['changed', 'text'], self._paged_display.page('main'))

        # Changes don't get pushed until explicitly pushed or active page set.
        self.assertEqual([list('main            '),
                          list('page            ')],
                         self._pushed)

    def test_temporaryPage_properlyShowsAndRevertsToActivePageContent(self):
        self._paged_display.page('main')[0] = 'main'
        self._paged_display.page('main')[1] = 'page'
        self._paged_display.set_active_page('main')

        self._paged_display.page('tmp')[0] = 'temporary'
        self._paged_display.page('tmp')[1] = 'toast'
        self._paged_display.set_active_page('tmp', expiration_ms=500)

        self.assertEqual(list('temporary       '), self._display[0])
        self.assertEqual(list('toast           '), self._display[1])
        self.assertEqual(['temporary', 'toast'],
                         self._paged_display.page('tmp'))
        self.assertEqual('temporary', self._paged_display[0])
        self.assertEqual('toast', self._paged_display[1])

        self.assertEqual([list('temporary       '),
                          list('toast           ')],
                         self._pushed)

        # No changes if the expiration time doesn't hit
        self._clock.advance(0.499)
        self._scheduler.idle()

        self.assertEqual('temporary', self._paged_display[0])
        self.assertEqual('toast', self._paged_display[1])
        self.assertEqual([list('temporary       '),
                          list('toast           ')],
                         self._pushed)

        # When expires, content reverts to main page
        self._clock.advance(0.001)
        self._scheduler.idle()

        self.assertEqual('main', self._paged_display[0])
        self.assertEqual('page', self._paged_display[1])
        self.assertEqual([list('main            '),
                          list('page            ')],
                         self._pushed)

    def test_temporaryPage_properlyShowsAndRevertsToActivePageContent(self):
        self._paged_display.page('main')[0] = 'main'
        self._paged_display.page('main')[1] = 'page'
        self._paged_display.set_active_page('main')

        self._paged_display.page('tmp')[0] = 'temporary'
        self._paged_display.page('tmp')[1] = 'toast'
        self._paged_display.set_active_page('tmp', expiration_ms=500)

        self.assertEqual(list('temporary       '), self._display[0])
        self.assertEqual(list('toast           '), self._display[1])
        self.assertEqual(['temporary', 'toast'],
                         self._paged_display.page('tmp'))
        self.assertEqual('temporary', self._paged_display[0])
        self.assertEqual('toast', self._paged_display[1])

        self.assertEqual([list('temporary       '),
                          list('toast           ')],
                         self._pushed)

        # No changes if the expiration time doesn't hit
        self._clock.advance(0.499)
        self._scheduler.idle()

        self.assertEqual('temporary', self._paged_display[0])
        self.assertEqual('toast', self._paged_display[1])
        self.assertEqual([list('temporary       '),
                          list('toast           ')],
                         self._pushed)

        # When expires, content reverts to main page
        self._clock.advance(0.001)
        self._scheduler.idle()

        self.assertEqual('main', self._paged_display[0])
        self.assertEqual('page', self._paged_display[1])
        self.assertEqual([list('main            '),
                          list('page            ')],
                         self._pushed)

    def test_temporaryPageWhileTemporaryPageActive_cancelsFirstProperly(self):
        self._paged_display.page('main')[0] = 'main'
        self._paged_display.page('main')[1] = 'page'
        self._paged_display.set_active_page('main')

        self._paged_display.page('tmp')[0] = 'temporary'
        self._paged_display.page('tmp')[1] = 'toast'
        self._paged_display.set_active_page('tmp', expiration_ms=500)

        self._paged_display.page('tmp2')[0] = 'another'
        self._paged_display.page('tmp2')[1] = 'msg'
        self._paged_display.set_active_page('tmp2', expiration_ms=100)

        self.assertEqual(list('another         '), self._display[0])
        self.assertEqual(list('msg             '), self._display[1])
        self.assertEqual('another', self._paged_display[0])
        self.assertEqual('msg', self._paged_display[1])

        self.assertEqual([list('another         '),
                          list('msg             ')],
                         self._pushed)

        # No changes if the expiration time doesn't hit
        self._clock.advance(0.100)
        self._scheduler.idle()

        self.assertEqual('main', self._paged_display[0])
        self.assertEqual('page', self._paged_display[1])
        self.assertEqual([list('main            '),
                          list('page            ')],
                         self._pushed)

        # When previous toast would have expire, nothing changes
        self._clock.advance(0.500)
        self._scheduler.idle()

        self.assertEqual('main', self._paged_display[0])
        self.assertEqual('page', self._paged_display[1])
        self.assertEqual([list('main            '),
                          list('page            ')],
                         self._pushed)

    def test_temporaryPageResetWhileActive_cancelsAndResetsProperly(self):
        self._paged_display.page('main')[0] = 'main'
        self._paged_display.page('main')[1] = 'page'
        self._paged_display.set_active_page('main')

        self._paged_display.page('tmp')[0] = 'temporary'
        self._paged_display.page('tmp')[1] = 'toast'
        self._paged_display.set_active_page('tmp', expiration_ms=500)
        self._paged_display.reset()

        self.assertEqual('main', self._paged_display[0])
        self.assertEqual('page', self._paged_display[1])
        self.assertEqual([list('main            '),
                          list('page            ')],
                         self._pushed)

        # Update active tab before the toast would have expired
        self._paged_display.page('new')[0] = 'hello'
        self._paged_display.page('new')[1] = 'world'
        self._paged_display.set_active_page('new')

        # When previous toast would have expire, nothing changes
        self._clock.advance(0.500)
        self._scheduler.idle()

        self.assertEqual('hello', self._paged_display[0])
        self.assertEqual('world', self._paged_display[1])
        self.assertEqual([list('hello           '),
                          list('world           ')],
                         self._pushed)


if __name__ == '__main__':
    unittest.main()
