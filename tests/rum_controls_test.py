import sys
import unittest

sys.path.insert(0, '..')
from rum_controls import BlinkableLight, Metronome
from rum_lights import OnOffLight
from rum_threading import Scheduler
from tests.testutils import FakeClock


class BlinkableLightsTest(unittest.TestCase):
    def setUp(self):
        self._on_count = 0
        self._off_count = 0

        def turn_on(): self._on_count += 1
        def turn_off(): self._off_count += 1

        self._light = OnOffLight(on_fn=turn_on, off_fn=turn_off)
        self._clock = FakeClock()
        self._scheduler = Scheduler(time_fn=self._clock.time)
        self._blinkable_light = BlinkableLight(self._light, self._scheduler,
                                               blink_interval_ms=1000)

    def test_toggleBlinkable_functionsAsRegularLight(self):
        self._blinkable_light.set(False, force_update=True)
        self._blinkable_light.toggle(bool_value=False)
        self.assertFalse(self._blinkable_light)
        self.assertFalse(self._light)
        self.assertEqual(1, self._off_count)
        self.assertEqual(0, self._on_count)

        self._blinkable_light.toggle()
        self.assertTrue(self._blinkable_light)
        self.assertTrue(self._light)
        self.assertEqual(1, self._off_count)
        self.assertEqual(1, self._on_count)

    def test_startBlinking_lightBlinks(self):
        self._blinkable_light.toggle(bool_value=False)
        self._blinkable_light.start_blinking()
        self.assertEqual(0, self._on_count + self._off_count)

        self._scheduler.idle()
        self.assertEqual(0, self._on_count + self._off_count)
        # Verify the interval
        self._clock.advance(0.999)
        self._scheduler.idle()
        self.assertEqual(0, self._on_count + self._off_count)

        # Verify the interval
        self._clock.advance(0.001)
        self._scheduler.idle()
        self.assertEqual(1, self._on_count)
        self.assertEqual(0, self._off_count)

        # Verify blink
        self._clock.advance(1)
        self._scheduler.idle()
        self.assertEqual(1, self._on_count)
        self.assertEqual(1, self._off_count)

        # Verify blink
        self._clock.advance(1)
        self._scheduler.idle()
        self.assertEqual(2, self._on_count)
        self.assertEqual(1, self._off_count)

    def test_lightsBlinking_stopBlinkStops(self):
        self._blinkable_light.toggle(bool_value=False)
        self._blinkable_light.start_blinking()
        for i in range(10):
            if i == 5:
                self._blinkable_light.stop_blinking()
            self._clock.advance(1)
            self._scheduler.idle()

        self.assertEqual(5, self._on_count + self._off_count)
        # Difference between on and off count should be no more than 1
        self.assertLessEqual(abs(self._on_count - self._off_count), 1)


class MetronomeTest(unittest.TestCase):
    def setUp(self):
        # Let's make a row of 5 lights
        self._data = [1 if idx % 2 == 0 else 0 for idx in range(5)]
        # And also lights that flip each entry
        self._lights = []

        def make_light(idx, data):
            def on_fn(): data[idx] = 1
            def off_fn(): data[idx] = 0
            # Have half the lights flipped on and half off.
            return OnOffLight(on_fn=on_fn, off_fn=off_fn,
                              initial=(idx % 2 == 0))

        for i in range(len(self._data)):
            self._lights.append(make_light(i, self._data))
        self._clock = FakeClock()
        self._scheduler = Scheduler(time_fn=self._clock.time)
        self._metronome = Metronome(self._scheduler, self._lights)

    def test_metronomeBeats_lightsResetAfterFirstBeat(self):
        self._metronome.beat()
        self.assertEqual([1, 0, 0, 0, 0], self._data)

    def test_metronomeLoops_lightsLoopProperly(self):
        history = []
        for i in range(7):
            self._metronome.beat()
            history.append(self._data[:])
        self.assertEqual([[1, 0, 0, 0, 0],
                          [0, 1, 0, 0, 0],
                          [0, 0, 1, 0, 0],
                          [0, 0, 0, 1, 0],
                          [0, 0, 0, 0, 1],
                          [1, 0, 0, 0, 0],
                          [0, 1, 0, 0, 0]], history)

    def test_metronomeResetInMiddle_startsFromFirstProperly(self):
        history = []
        for i in range(7):
            if i == 3:
                self._metronome.reset()
            self._metronome.beat()
            history.append(self._data[:])
        self.assertEqual([[1, 0, 0, 0, 0],
                          [0, 1, 0, 0, 0],
                          [0, 0, 1, 0, 0],
                          [1, 0, 0, 0, 0],
                          [0, 1, 0, 0, 0],
                          [0, 0, 1, 0, 0],
                          [0, 0, 0, 1, 0]], history)


if __name__ == '__main__':
    unittest.main()
