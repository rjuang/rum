import sys
import unittest

sys.path.insert(0, '..')
from rum_animation import BlinkingAnimation, SequentialAnimation
from rum_lights import OnOffLight
from rum_threading import Scheduler
from tests.testutils import FakeClock


class BlinkingAnimationTest(unittest.TestCase):
    def setUp(self):
        self._light = OnOffLight()
        self._clock = FakeClock()
        self._scheduler = Scheduler(time_fn=self._clock.time)
        self._animation = BlinkingAnimation(self._light, self._scheduler,
                                            update_interval_ms=250)

    def test_blinkingAnimation_doesNotAnimateIfNotStarted(self):
        self.assertFalse(self._light)
        self._clock.advance(0.5)
        self._scheduler.idle()
        self.assertFalse(self._light)

    def test_blinkingAnimation_blinkingAnimationAfterStart(self):
        self._animation.start()
        self.assertFalse(self._light)
        # Test 5 iterations of blinking
        for _ in range(5):
            self._clock.advance(0.250)
            self._scheduler.idle()
            self.assertTrue(self._light)

            self._clock.advance(0.250)
            self._scheduler.idle()
            self.assertFalse(self._light)

    def test_whenAnimationStarted_stopBlinkingStops(self):
        self._animation.start()

        self._clock.advance(0.750)
        self._scheduler.idle()
        self._animation.stop()
        self.assertTrue(self._light)

        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertTrue(self._light)

    def test_whenAnimationStartedStopped_startBlinkingStarts(self):
        self._animation.start()
        self._clock.advance(0.750)
        self._scheduler.idle()
        self._animation.stop()
        self._animation.start()

        # Light should be on before we step through time
        self.assertTrue(self._light)
        self._clock.advance(0.250)
        self._scheduler.idle()
        # Animation should toggle light off
        self.assertFalse(self._light)

        self._clock.advance(0.250)
        self._scheduler.idle()
        # Animation should toggle light back on
        self.assertTrue(self._light)


class SequentialAnimationTest(unittest.TestCase):
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
        self._animation = SequentialAnimation(
            [[self._lights[i]] for i in range(len(self._lights))],
            self._scheduler,
            update_interval_ms=250,
            loop=True)

    def test_animationNotStarted_initialStateCorrect(self):
        self.assertEqual([1, 0, 1, 0, 1], self._data)
        self.assertFalse(self._animation.is_running())

    def test_animationStarted_isRunningReturnsTrue(self):
        self._animation.start()
        self.assertTrue(self._animation.is_running())
        self.assertEqual([1, 0, 1, 0, 1], self._data)

    def test_animationStopped_isRunningReturnsFalse(self):
        self._animation.start()
        self._animation.stop()
        self.assertFalse(self._animation.is_running())
        self.assertEqual([1, 0, 1, 0, 1], self._data)

    def test_animationStarted_firstFrameAnimatesImmediately(self):
        self._animation.start()
        self._scheduler.idle()
        self.assertEqual([1, 0, 0, 0, 0], self._data)

    def test_animationStarted_secondFramesAndOnwardsSpacedAppropriately(self):
        self._animation.start()
        self._scheduler.idle()
        self._scheduler.idle()

        # Clock doesn't advance so should not result in anything
        self.assertEqual([1, 0, 0, 0, 0], self._data)

        # Step one animation interval
        pattern = []
        for _ in range(5):
            self._clock.advance(0.250)
            self._scheduler.idle()
            pattern.append(self._data[:])

        self.assertEqual(
            [[0, 1, 0, 0, 0],
             [0, 0, 1, 0, 0],
             [0, 0, 0, 1, 0],
             [0, 0, 0, 0, 1],
             [1, 0, 0, 0, 0]],
            pattern)

    def test_animationStarted_animationTurnsOffLightsAtLoopCorrectly(self):
        self._animation.start()
        self._scheduler.idle()
        self._scheduler.idle()

        # Clock doesn't advance so should not result in anything
        self.assertEqual([1, 0, 0, 0, 0], self._data)

        # Step one animation interval
        pattern = []
        for _ in range(3):
            self._clock.advance(0.250)
            self._scheduler.idle()
            pattern.append(self._data[:])

        # Before looping, a light that would stay off randomly flips on
        self._lights[1].toggle(bool_value=True)
        for _ in range(2):
            self._clock.advance(0.250)
            self._scheduler.idle()
        self.assertEqual([1, 0, 0, 0, 0], self._data)

    def test_animationStopped_animationNoLongerContinues(self):
        self._animation.start()
        self._scheduler.idle()
        self._clock.advance(0.250)
        self._scheduler.idle()
        self._animation.stop()

        for _ in range(2):
            self._clock.advance(0.250)
            self._scheduler.idle()
        # Light pattern is fixed at last stopped pattern.
        self.assertEqual([0, 1, 0, 0, 0], self._data)

    def test_animationRestarted_animationShouldPickUpFromWhereItLeftOff(self):
        self._animation.start()
        self._scheduler.idle()

        # Advance one frame before stopping
        self._clock.advance(0.250)
        self._scheduler.idle()
        self._animation.stop()

        # Random advancing.
        for _ in range(2):
            self._clock.advance(0.250)
            self._scheduler.idle()

        self._animation.start(initial_delay=True)
        self._scheduler.idle()
        # Light pattern should be where it left off
        self.assertEqual([0, 1, 0, 0, 0], self._data)

        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual([0, 0, 1, 0, 0], self._data)

        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual([0, 0, 0, 1, 0], self._data)

        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual([0, 0, 0, 0, 1], self._data)

        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual([1, 0, 0, 0, 0], self._data)

    def test_resetAnimation_restartsFromBeginning(self):
        self._animation.start()
        self._scheduler.idle()

        # Advance one frame before stopping
        self._clock.advance(0.250)
        self._scheduler.idle()
        self._animation.stop()

        # Random advancing.
        for _ in range(2):
            self._clock.advance(0.250)
            self._scheduler.idle()

        self._animation.reset()
        self._animation.start()
        self._scheduler.idle()
        # Light pattern should be where it left off
        self.assertEqual([1, 0, 0, 0, 0], self._data)

        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual([0, 1, 0, 0, 0], self._data)

        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual([0, 0, 1, 0, 0], self._data)

        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual([0, 0, 0, 1, 0], self._data)

        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual([0, 0, 0, 0, 1], self._data)

        self._clock.advance(0.250)
        self._scheduler.idle()
        self.assertEqual([1, 0, 0, 0, 0], self._data)


if __name__ == '__main__':
    unittest.main()
