import sys
import unittest

sys.path.insert(0, '..')
from rum.recorder import Recorder
from rum.scheduling import Scheduler
from tests.testutils import FakeClock


class RecorderTests(unittest.TestCase):
    def setUp(self):
        self._data_played = []

        def playback_fn(data):
            self._data_played.append(data)

        self._clock = FakeClock()
        self._scheduler = Scheduler(time_fn=self._clock.time)
        self._recorder = Recorder(self._scheduler, playback_fn=playback_fn)

    def _feed_pattern(self, start_timestamp, data):
        # Space out each event by 1 second.
        for i, values in enumerate(data):
            for v in values:
                self._recorder.on_data_event(1000 * i + start_timestamp, v)

    def _feed_odd_pattern(self, start_timestamp):
        # The tuple represents simultaneous events (e.g. piano chord)
        data = [(i, 10 + i) for i in range(1, 10, 2)]
        self._feed_pattern(start_timestamp, data)
        return len(data)

    def _feed_even_pattern(self, start_timestamp):
        # The tuple represents simultaneous events (e.g. piano chord)
        data = [(i, 10 + i) for i in range(0, 10, 2)]
        self._feed_pattern(start_timestamp, data)
        return len(data)

    def test_isRecordingWhileAfterInit_returnsFalse(self):
        self.assertEqual(False, self._recorder.is_recording())

    def test_getRecordingPatternIdAfterInit_returnsNone(self):
        self.assertEqual(None, self._recorder.get_recording_pattern_id())

    def test_isRecordingWhileAfterStopped_returnsFalse(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()
        self.assertEqual(False, self._recorder.is_recording())

    def test_getRecordingPatternIdAfterStopped_returnsNone(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()
        self.assertEqual(None, self._recorder.get_recording_pattern_id())

    def test_isRecordingAfterStart_returnsTrue(self):
        self._recorder.start_recording('even')
        self.assertEqual(True, self._recorder.is_recording())

    def test_getRecordingPatternAfterStart_returnsId(self):
        self._recorder.start_recording('even')
        self.assertEqual('even', self._recorder.get_recording_pattern_id())

    def test_playWithNoRecording_playbackReturnsFalse(self):
        self._feed_even_pattern(1000)
        self.assertFalse(self._recorder.play('non-existent-id'))
        self.assertFalse(self._recorder.play('non-existent-id', loop=True))
        self.assertEqual([], self._data_played)

    def test_recordAndPlayNonexistentPattern_noPlaybackOnDifferentPattern(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()
        self.assertFalse(self._recorder.play('non-existent-id'))
        self.assertFalse(self._recorder.play('non-existent-id', loop=True))
        self.assertEqual([], self._data_played)

    def test_playRecordedPattern_playbackPlaysOnce(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()
        self._feed_odd_pattern(6000)

        result = self._recorder.play('even')
        self.assertEqual(True, result)

        # Make sure notes are played back correctly in time.
        history = []

        self._scheduler.idle()
        history.append(self._data_played[:])

        for _ in range(6):
            # Each step is 1 second
            self._clock.advance(1)
            self._scheduler.idle()
            history.append(self._data_played[:])

        self.assertEqual([
            [0, 10],           # Before loop, first idle call
            [0, 10, 2, 12],    # Loop 0
            [0, 10, 2, 12, 4, 14],
            [0, 10, 2, 12, 4, 14, 6, 16],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18],  # No new notes expected after.
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18]],
            history)

    def test_playRecordedPatternWithLoop_playbackLoops(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()
        self._feed_odd_pattern(6000)

        result = self._recorder.play('even', loop=True, loop_delay_ms=0)
        self.assertEqual(True, result)

        # Make sure notes are played back correctly in time.
        history = []

        self._scheduler.idle()
        history.append(self._data_played[:])

        for _ in range(6):
            # Each step is 1 second
            self._clock.advance(1)
            self._scheduler.idle()
            history.append(self._data_played[:])

        self.assertEqual([
            [0, 10],           # Before loop, first idle call
            [0, 10, 2, 12],    # Loop 0
            [0, 10, 2, 12, 4, 14],
            [0, 10, 2, 12, 4, 14, 6, 16],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18, 0, 10],   # no loop delay
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18, 0, 10, 2, 12],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18, 0, 10, 2, 12, 4, 14]],
            history)

    def test_playRecordedPatternWithLoopAndLoopDelay_playLoopsWithDelay(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()
        self._feed_odd_pattern(6000)

        result = self._recorder.play('even', loop=True, loop_delay_ms=1000)
        self.assertEqual(True, result)

        # Make sure notes are played back correctly in time.
        history = []

        self._scheduler.idle()
        history.append(self._data_played[:])

        for _ in range(6):
            # Each step is 1 second
            self._clock.advance(1)
            self._scheduler.idle()
            history.append(self._data_played[:])

        self.assertEqual([
            [0, 10],           # Before loop, first idle call
            [0, 10, 2, 12],    # Loop 0
            [0, 10, 2, 12, 4, 14],
            [0, 10, 2, 12, 4, 14, 6, 16],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18],         # w/ loop delay
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18, 0, 10],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18, 0, 10, 2, 12]],
            history)

    def test_playMultipleRecordedPattern_playbackWorks(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()

        self._recorder.start_recording('odd')
        self._feed_odd_pattern(6000)
        self._recorder.stop_recording()

        result = self._recorder.play('even')
        self.assertEqual(True, result)

        result = self._recorder.play('odd')
        self.assertEqual(True, result)

        # Make sure notes are played back correctly in time.
        history = []

        self._scheduler.idle()
        history.append(self._data_played[:])

        for _ in range(6):
            # Each step is 1 second
            self._clock.advance(1)
            self._scheduler.idle()
            history.append(self._data_played[:])

        # The notes will be jumbled, so we need to filter them out by even and
        # odds and compare
        even_history = [[v for v in data if v % 2 == 0] for data in history]
        odd_history = [[v for v in data if v % 2 == 1] for data in history]

        self.assertEqual([
            [0, 10],           # Before loop, first idle call
            [0, 10, 2, 12],    # Loop 0
            [0, 10, 2, 12, 4, 14],
            [0, 10, 2, 12, 4, 14, 6, 16],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18],  # No new notes expected after.
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18]],
            even_history)

        self.assertEqual([
            [1, 11],           # Before loop, first idle call
            [1, 11, 3, 13],    # Loop 0
            [1, 11, 3, 13, 5, 15],
            [1, 11, 3, 13, 5, 15, 7, 17],
            [1, 11, 3, 13, 5, 15, 7, 17, 9, 19],  # No new notes expected after.
            [1, 11, 3, 13, 5, 15, 7, 17, 9, 19],
            [1, 11, 3, 13, 5, 15, 7, 17, 9, 19]],
            odd_history)

    def test_playMultiplePatternsOneLoops_oneLoopsAndOtherDoesnt(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()

        self._recorder.start_recording('odd')
        self._feed_odd_pattern(6000)
        self._recorder.stop_recording()

        result = self._recorder.play('even', loop=True, loop_delay_ms=1000)
        self.assertEqual(True, result)

        result = self._recorder.play('odd')
        self.assertEqual(True, result)

        # Make sure notes are played back correctly in time.
        history = []

        self._scheduler.idle()
        history.append(self._data_played[:])

        for _ in range(6):
            # Each step is 1 second
            self._clock.advance(1)
            self._scheduler.idle()
            history.append(self._data_played[:])

        # The notes will be jumbled, so we need to filter them out by even and
        # odds and compare
        even_history = [[v for v in data if v % 2 == 0] for data in history]
        odd_history = [[v for v in data if v % 2 == 1] for data in history]

        self.assertEqual([
            [0, 10],           # Before loop, first idle call
            [0, 10, 2, 12],    # Loop 0
            [0, 10, 2, 12, 4, 14],
            [0, 10, 2, 12, 4, 14, 6, 16],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18],         # w/ loop delay
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18, 0, 10],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18, 0, 10, 2, 12]],
            even_history)

        self.assertEqual([
            [1, 11],           # Before loop, first idle call
            [1, 11, 3, 13],    # Loop 0
            [1, 11, 3, 13, 5, 15],
            [1, 11, 3, 13, 5, 15, 7, 17],
            [1, 11, 3, 13, 5, 15, 7, 17, 9, 19],  # No new notes expected after.
            [1, 11, 3, 13, 5, 15, 7, 17, 9, 19],
            [1, 11, 3, 13, 5, 15, 7, 17, 9, 19]],
            odd_history)

    def test_stopWhilePlayRecordedPattern_successfullyStops(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()
        self._feed_odd_pattern(6000)

        result = self._recorder.play('even')
        self.assertEqual(True, result)

        # Make sure notes are played back correctly in time.
        history = []

        self._scheduler.idle()
        history.append(self._data_played[:])

        for i in range(6):
            if i == 3:
                self._recorder.stop('even')
            # Each step is 1 second
            self._clock.advance(1)
            self._scheduler.idle()
            history.append(self._data_played[:])

        self.assertEqual([
            [0, 10],           # Before loop, first idle call
            [0, 10, 2, 12],    # Loop 0
            [0, 10, 2, 12, 4, 14],
            [0, 10, 2, 12, 4, 14, 6, 16],  # Loop 2. Stops before loop 3
            [0, 10, 2, 12, 4, 14, 6, 16],
            [0, 10, 2, 12, 4, 14, 6, 16],
            [0, 10, 2, 12, 4, 14, 6, 16]],
            history)

    def test_stopWhilePlayingMultipleRecordedPattern_stopsOneOtherPlays(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()

        self._recorder.start_recording('odd')
        self._feed_odd_pattern(6000)
        self._recorder.stop_recording()

        result = self._recorder.play('even')
        self.assertEqual(True, result)

        result = self._recorder.play('odd')
        self.assertEqual(True, result)

        # Make sure notes are played back correctly in time.
        history = []

        self._scheduler.idle()
        history.append(self._data_played[:])

        for i in range(6):
            if i == 3:
                self._recorder.stop('even')
            # Each step is 1 second
            self._clock.advance(1)
            self._scheduler.idle()
            history.append(self._data_played[:])

        # The notes will be jumbled, so we need to filter them out by even and
        # odds and compare
        even_history = [[v for v in data if v % 2 == 0] for data in history]
        odd_history = [[v for v in data if v % 2 == 1] for data in history]

        # Even wil stop after loop 2
        self.assertEqual([
            [0, 10],           # Before loop, first idle call
            [0, 10, 2, 12],    # Loop 0
            [0, 10, 2, 12, 4, 14],
            [0, 10, 2, 12, 4, 14, 6, 16],  # Loop 2. Stopped after this.
            [0, 10, 2, 12, 4, 14, 6, 16],
            [0, 10, 2, 12, 4, 14, 6, 16],
            [0, 10, 2, 12, 4, 14, 6, 16]],
            even_history)

        self.assertEqual([
            [1, 11],           # Before loop, first idle call
            [1, 11, 3, 13],    # Loop 0
            [1, 11, 3, 13, 5, 15],
            [1, 11, 3, 13, 5, 15, 7, 17],
            [1, 11, 3, 13, 5, 15, 7, 17, 9, 19],  # No new notes expected after.
            [1, 11, 3, 13, 5, 15, 7, 17, 9, 19],
            [1, 11, 3, 13, 5, 15, 7, 17, 9, 19]],
            odd_history)

    def test_stopNonExistentPattern_noImpact(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()

        self._recorder.start_recording('odd')
        self._feed_odd_pattern(6000)
        self._recorder.stop_recording()

        result = self._recorder.play('even', loop=True, loop_delay_ms=1000)
        self.assertEqual(True, result)

        result = self._recorder.play('odd')
        self.assertEqual(True, result)

        # Make sure notes are played back correctly in time.
        history = []

        self._scheduler.idle()
        history.append(self._data_played[:])

        for _ in range(6):
            self._recorder.stop('non-existent-pattern')
            # Each step is 1 second
            self._clock.advance(1)
            self._scheduler.idle()
            history.append(self._data_played[:])

        # The notes will be jumbled, so we need to filter them out by even and
        # odds and compare
        even_history = [[v for v in data if v % 2 == 0] for data in history]
        odd_history = [[v for v in data if v % 2 == 1] for data in history]

        self.assertEqual([
            [0, 10],           # Before loop, first idle call
            [0, 10, 2, 12],    # Loop 0
            [0, 10, 2, 12, 4, 14],
            [0, 10, 2, 12, 4, 14, 6, 16],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18],         # w/ loop delay
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18, 0, 10],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18, 0, 10, 2, 12]],
            even_history)

        self.assertEqual([
            [1, 11],           # Before loop, first idle call
            [1, 11, 3, 13],    # Loop 0
            [1, 11, 3, 13, 5, 15],
            [1, 11, 3, 13, 5, 15, 7, 17],
            [1, 11, 3, 13, 5, 15, 7, 17, 9, 19],  # No new notes expected after.
            [1, 11, 3, 13, 5, 15, 7, 17, 9, 19],
            [1, 11, 3, 13, 5, 15, 7, 17, 9, 19]],
            odd_history)

    def test_stopAllWhileNotPlaying_noImpact(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()
        self._recorder.stop_all()
        self._clock.advance(1)
        self._scheduler.idle()
        self.assertEqual([], self._data_played)

    def test_stopAllWhilePlayingMultiple_stopsAll(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()

        self._recorder.start_recording('odd')
        self._feed_odd_pattern(6000)
        self._recorder.stop_recording()

        result = self._recorder.play('even', loop=True, loop_delay_ms=1000)
        self.assertEqual(True, result)

        result = self._recorder.play('odd')
        self.assertEqual(True, result)

        # Make sure notes are played back correctly in time.
        history = []

        self._scheduler.idle()
        history.append(self._data_played[:])

        for i in range(6):
            if i == 3:
                self._recorder.stop_all()
            self._clock.advance(1)
            self._scheduler.idle()
            history.append(self._data_played[:])

        # The notes will be jumbled, so we need to filter them out by even and
        # odds and compare
        even_history = [[v for v in data if v % 2 == 0] for data in history]
        odd_history = [[v for v in data if v % 2 == 1] for data in history]

        self.assertEqual([
            [0, 10],           # Before loop, first idle call
            [0, 10, 2, 12],    # Loop 0
            [0, 10, 2, 12, 4, 14],
            [0, 10, 2, 12, 4, 14, 6, 16],  # Loop 2. Stopped after this.
            [0, 10, 2, 12, 4, 14, 6, 16],
            [0, 10, 2, 12, 4, 14, 6, 16],
            [0, 10, 2, 12, 4, 14, 6, 16]],
            even_history)

        self.assertEqual([
            [1, 11],           # Before loop, first idle call
            [1, 11, 3, 13],    # Loop 0
            [1, 11, 3, 13, 5, 15],
            [1, 11, 3, 13, 5, 15, 7, 17],  # Loop 2. Stopped after this.
            [1, 11, 3, 13, 5, 15, 7, 17],
            [1, 11, 3, 13, 5, 15, 7, 17],
            [1, 11, 3, 13, 5, 15, 7, 17]],
            odd_history)

    def test_stopWhilePlayingLoop_stopsLoop(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()
        self._feed_odd_pattern(6000)

        result = self._recorder.play('even', loop=True)
        self.assertEqual(True, result)

        # Make sure notes are played back correctly in time.
        history = []

        self._scheduler.idle()
        history.append(self._data_played[:])

        for i in range(6):
            if i == 3:
                self._recorder.stop('even')
            # Each step is 1 second
            self._clock.advance(1)
            self._scheduler.idle()
            history.append(self._data_played[:])

        self.assertEqual([
            [0, 10],           # Before loop, first idle call
            [0, 10, 2, 12],    # Loop 0
            [0, 10, 2, 12, 4, 14],
            [0, 10, 2, 12, 4, 14, 6, 16],  # Loop 2. Stops before loop 3
            [0, 10, 2, 12, 4, 14, 6, 16],
            [0, 10, 2, 12, 4, 14, 6, 16],
            [0, 10, 2, 12, 4, 14, 6, 16]],
            history)

    def test_cancelLoopWhenNotLooping_finishes(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()
        self._feed_odd_pattern(6000)

        result = self._recorder.play('even')
        self.assertEqual(True, result)

        # Make sure notes are played back correctly in time.
        history = []

        self._scheduler.idle()
        history.append(self._data_played[:])

        for i in range(6):
            if i == 3:
                self._recorder.cancel_loop('even')
            # Each step is 1 second
            self._clock.advance(1)
            self._scheduler.idle()
            history.append(self._data_played[:])

        self.assertEqual([
            [0, 10],           # Before loop, first idle call
            [0, 10, 2, 12],    # Loop 0
            [0, 10, 2, 12, 4, 14],
            [0, 10, 2, 12, 4, 14, 6, 16],  # Loop 2. looping canceled.
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18]],
            history)

    def test_cancelLoopWhileLooping_loopStopsButPlaybackFinishes(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()
        self._feed_odd_pattern(6000)

        result = self._recorder.play('even', loop=True)
        self.assertEqual(True, result)

        # Make sure notes are played back correctly in time.
        history = []

        self._scheduler.idle()
        history.append(self._data_played[:])

        for i in range(6):
            if i == 3:
                self._recorder.cancel_loop('even')
            # Each step is 1 second
            self._clock.advance(1)
            self._scheduler.idle()
            history.append(self._data_played[:])

        self.assertEqual([
            [0, 10],           # Before loop, first idle call
            [0, 10, 2, 12],    # Loop 0
            [0, 10, 2, 12, 4, 14],
            [0, 10, 2, 12, 4, 14, 6, 16],  # Loop 2. looping canceled.
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18]],
            history)

    def test_cancelNonexistentLoopDuringLoopPlayback_noImpact(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()
        self._feed_odd_pattern(6000)

        result = self._recorder.play('even', loop=True, loop_delay_ms=1000)
        self.assertEqual(True, result)

        # Make sure notes are played back correctly in time.
        history = []

        self._scheduler.idle()
        history.append(self._data_played[:])

        for i in range(6):
            if i == 3:
                self._recorder.cancel_loop('non-existent-id')
            # Each step is 1 second
            self._clock.advance(1)
            self._scheduler.idle()
            history.append(self._data_played[:])

        self.assertEqual([
            [0, 10],           # Before loop, first idle call
            [0, 10, 2, 12],    # Loop 0
            [0, 10, 2, 12, 4, 14],
            [0, 10, 2, 12, 4, 14, 6, 16],  # Loop 2. looping canceled.
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18, 0, 10],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18, 0, 10, 2, 12]],
            history)

    def test_cancelLoopWhilePlayingMultiple_stopsOneOtherLoops(self):
        self._recorder.start_recording('even')
        self._feed_even_pattern(1000)
        self._recorder.stop_recording()

        self._recorder.start_recording('odd')
        self._feed_odd_pattern(6000)
        self._recorder.stop_recording()

        result = self._recorder.play('even', loop=True, loop_delay_ms=1000)
        self.assertEqual(True, result)

        result = self._recorder.play('odd', loop=True, loop_delay_ms=1000)
        self.assertEqual(True, result)

        # Make sure notes are played back correctly in time.
        history = []

        self._scheduler.idle()
        history.append(self._data_played[:])

        for i in range(6):
            if i == 3:
                self._recorder.cancel_loop('even')
            # Each step is 1 second
            self._clock.advance(1)
            self._scheduler.idle()
            history.append(self._data_played[:])

        # The notes will be jumbled, so we need to filter them out by even and
        # odds and compare
        even_history = [[v for v in data if v % 2 == 0] for data in history]
        odd_history = [[v for v in data if v % 2 == 1] for data in history]

        # Even wil stop after loop 2
        self.assertEqual([
            [0, 10],           # Before loop, first idle call
            [0, 10, 2, 12],    # Loop 0
            [0, 10, 2, 12, 4, 14],
            [0, 10, 2, 12, 4, 14, 6, 16],  # Loop 2. Stopped after this.
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18],
            [0, 10, 2, 12, 4, 14, 6, 16, 8, 18]],
            even_history)

        self.assertEqual([
            [1, 11],           # Before loop, first idle call
            [1, 11, 3, 13],    # Loop 0
            [1, 11, 3, 13, 5, 15],
            [1, 11, 3, 13, 5, 15, 7, 17],
            [1, 11, 3, 13, 5, 15, 7, 17, 9, 19],
            [1, 11, 3, 13, 5, 15, 7, 17, 9, 19, 1, 11],
            [1, 11, 3, 13, 5, 15, 7, 17, 9, 19, 1, 11, 3, 13]],
            odd_history)

    # TODO: Add tests for set_loop_delay
if __name__ == '__main__':
    unittest.main()
