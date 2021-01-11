from device_profile.abstract import MidiCommandBuilder


class Mk2(MidiCommandBuilder):
    """ MIDI Command structure for Arturia Keylab 61 mk2. """

    CMD_BEGIN = bytes([0xF0, 0x00, 0x20, 0x6B, 0x7F, 0x42])
    CMD_END = bytes([0xF7])
    # Light command is the below prefix followed by id1, val1, id2, val2, ...
    CMD_SET_LIGHTS = bytes([0x02, 0x00, 0x10])
    CMD_SET_DISPLAY = bytes([0x04, 0x00, 0x60])

    def build(self):
        # Start with the lights
        cmd = bytes()
        if (self.param_lights_to_turn_off
                or self.param_lights_to_turn_on
                or self.param_lights_to_set_colors):
            cmd += Mk2.CMD_BEGIN
            cmd += Mk2.CMD_SET_LIGHTS
            for led_id in self.param_lights_to_turn_off:
                cmd += bytes([led_id, 0])

            for led_id in self.param_lights_to_turn_on:
                cmd += bytes([led_id, 0x7F])

            for led_id, led_value in self.param_lights_to_set_colors:
                cmd += bytes([led_id, led_value])
            cmd += Mk2.CMD_END

        # Now deal with the display
        if self.param_display_updates:
            # Keylab 61 only has 1 display, so just fetch the last update.
            lines = self.param_display_updates[-1]
            cmd += Mk2.CMD_BEGIN
            cmd += Mk2.CMD_SET_DISPLAY
            cmd += bytes([0x1]) + bytes(lines[0], 'ascii') + bytes([0x00])
            if len(lines) >= 2:
                cmd += bytes([0x2]) + bytes(lines[1], 'ascii') + bytes([0x00])
            cmd += bytes([0x7F])
            cmd += Mk2.CMD_END
        return cmd
