import sys
import unittest

sys.path.insert(0, '..')
from rum_animation import BlinkingAnimation
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
        self._clock.advance_by(0.5)
        self._scheduler.idle()
        self.assertFalse(self._light)

    def test_blinkingAnimation_blinkingAnimationAfterStart(self):
        self._animation.start()
        self.assertFalse(self._light)
        # Test 5 iterations of blinking
        for _ in range(5):
            self._clock.advance_by(0.250)
            self._scheduler.idle()
            self.assertTrue(self._light)

            self._clock.advance_by(0.250)
            self._scheduler.idle()
            self.assertFalse(self._light)

    def test_whenAnimationStarted_stopBlinkingStops(self):
        self._animation.start()

        self._clock.advance_by(0.750)
        self._scheduler.idle()
        self._animation.stop()
        self.assertTrue(self._light)

        self._clock.advance_by(0.250)
        self._scheduler.idle()
        self.assertTrue(self._light)

    def test_whenAnimationStartedStopped_startBlinkingStarts(self):
        self._animation.start()
        self._clock.advance_by(0.750)
        self._scheduler.idle()
        self._animation.stop()
        self._animation.start()

        # Light should be on before we step through time
        self.assertTrue(self._light)
        self._clock.advance_by(0.250)
        self._scheduler.idle()
        # Animation should toggle light off
        self.assertFalse(self._light)

        self._clock.advance_by(0.250)
        self._scheduler.idle()
        # Animation should toggle light back on
        self.assertTrue(self._light)


if __name__ == '__main__':
    unittest.main()
