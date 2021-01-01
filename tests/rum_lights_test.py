import sys
import unittest

sys.path.insert(0, '..')
from rum_lights import OnOffLight, ColorLight, ColorToggleLight


class OnOffLightTests(unittest.TestCase):
    def setUp(self):
        self._on_count = 0
        self._off_count = 0

        def turn_on(): self._on_count += 1
        def turn_off(): self._off_count += 1

        self._light = OnOffLight(on_fn=turn_on, off_fn=turn_off)

    def test_initialState_verifyStateAndNoCommandsSent(self):
        self.assertFalse(self._light)
        self.assertEqual(False, self._light.get())
        self.assertEqual(0, self._on_count)
        self.assertEqual(0, self._off_count)

    def test_toggleState_verifyUpdatedStateAndCommandSent(self):
        self._light.toggle()
        self.assertTrue(self._light)
        self.assertTrue(self._light.get())
        self.assertEqual(1, self._on_count)
        self.assertEqual(0, self._off_count)

    def test_setOffFromInitialState_doesNotSendExtraUpdate(self):
        self._light.set(False)
        self.assertFalse(self._light)
        self.assertFalse(self._light.get())
        self.assertEqual(0, self._on_count)
        self.assertEqual(0, self._off_count)

    def test_setOnAfterToggle_doesNotSendExtraUpdate(self):
        self._light.toggle()
        self._light.set(True)
        self.assertTrue(self._light)
        self.assertTrue(self._light.get())
        self.assertEqual(1, self._on_count)
        self.assertEqual(0, self._off_count)

    def test_setSameStateWithForcedUpdate_sendsUpdate(self):
        self._light.toggle()
        self._light.set(True, force_update=True)
        self.assertTrue(self._light)
        self.assertTrue(self._light.get())
        self.assertEqual(2, self._on_count)
        self.assertEqual(0, self._off_count)

    def test_setValueWithToggleKeyword_setsValueAppropriately(self):
        self._light.toggle(bool_value=False)
        self.assertFalse(self._light)
        self.assertFalse(self._light.get())
        self.assertEqual(0, self._on_count)
        self.assertEqual(0, self._off_count)

        self._light.toggle(bool_value=False)
        self.assertFalse(self._light)
        self.assertFalse(self._light.get())
        self.assertEqual(0, self._on_count)
        self.assertEqual(0, self._off_count)

        self._light.toggle(bool_value=True)
        self.assertTrue(self._light)
        self.assertTrue(self._light.get())
        self.assertEqual(1, self._on_count)
        self.assertEqual(0, self._off_count)

        self._light.toggle(bool_value=True)
        self.assertTrue(self._light)
        self.assertTrue(self._light.get())
        self.assertEqual(1, self._on_count)
        self.assertEqual(0, self._off_count)



class ColorLightTests(unittest.TestCase):
    def setUp(self):
        self._update_values = []
        def update_fn(value): self._update_values.append(value)
        self._light = ColorLight(update_fn=update_fn)

    def test_initialState_hasCorrectStateAndNoCommandsSent(self):
        self.assertFalse(self._light)
        self.assertEqual(0, self._light.get())
        self.assertEqual(0, len(self._update_values))

    def test_setDifferentValue_updatesNewValueSendsCommand(self):
        self._light.set(15)
        self.assertTrue(self._light)
        self.assertEqual(15, self._light.get())
        self.assertEqual([15], self._update_values)

        self._light.set(16)
        self.assertTrue(self._light)
        self.assertEqual(16, self._light.get())
        self.assertEqual([15, 16], self._update_values)

    def test_setSameValue_noAdditionalCommandsSent(self):
        self._light.set(15)
        self._light.set(15)
        self.assertTrue(self._light)
        self.assertEqual(15, self._light.get())
        self.assertEqual([15], self._update_values)


class ColorToggleLightsTest(unittest.TestCase):
    def setUp(self):
        self._update_values = []
        def update_fn(value): self._update_values.append(value)
        light = ColorLight(update_fn=update_fn, initial=15)
        self._light = ColorToggleLight(light, off_color=15, on_color=30)

    def test_whenColorIsEquivalentToOffColor_toggleFlipsToOn(self):
        self.assertEqual(True, self._light.toggle())
        self.assertEqual(30, self._light.get())
        self.assertTrue(self._light)
        self.assertEqual([30], self._update_values)

    def test_whenColorIsEquivalentToOnColor_toggleFlipsToOff(self):
        self._light.toggle()
        self.assertEqual(False, self._light.toggle())
        self.assertEqual(15, self._light.get())
        self.assertFalse(self._light)
        self.assertEqual([30, 15], self._update_values)

    def test_whenToggleColorsWithSpecifiedValue_checkCorrectValue(self):
        self.assertFalse(self._light.toggle(bool_value=False))
        self.assertFalse(self._light.toggle(bool_value=False))
        self.assertEqual(15, self._light.get())
        self.assertFalse(self._light)
        self.assertEqual([], self._update_values)

        self.assertTrue(self._light.toggle(bool_value=True))
        self.assertEqual(30, self._light.get())
        self.assertTrue(self._light)
        self.assertEqual([30], self._update_values)
        self.assertTrue(self._light.toggle(bool_value=True))
        self.assertEqual(30, self._light.get())
        self.assertTrue(self._light)
        self.assertEqual([30], self._update_values)


if __name__ == '__main__':
    unittest.main()
