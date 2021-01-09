import unittest

from device_profile.command import MidiCommandBuilder


class MidiCommandBuilderTest(unittest.TestCase):
    class TestCommandBuilder(MidiCommandBuilder):
        def build(self):
            return b''

    def setUp(self):
        self._command_builder = MidiCommandBuilderTest.TestCommandBuilder()

    def test_addLightsOn_properlySet(self):
        self._command_builder.light_on(1, 2, 3, 4).build()
        self.assertEqual([1,2,3,4],
                         self._command_builder.param_lights_to_turn_on)

    def test_addLightsOff_properlySet(self):
        self._command_builder.light_off(1, 2, 3, 4).build()
        self.assertEqual(
            [1,2,3,4],
            self._command_builder.param_lights_to_turn_off)

    def test_addLightColor_properlySet(self):
        self._command_builder.light_color(1, 10, 2, 12, 3, 13).build()
        self.assertEqual(
            [(1, 10), (2, 12), (3, 13)],
            self._command_builder.param_lights_to_set_colors)

    def test_displayLines_properlySet(self):
        (self._command_builder
         .display(0, ['hello', 'world'])
         .display(1, ['volume'])
         .display(2, ['cat'])
         .build())

        self.assertEqual([
            (0, ['hello', 'world']),
            (1, ['volume']),
            (2, ['cat'])],
            self._command_builder.param_display_updates)


if __name__ == '__main__':
    unittest.main()
