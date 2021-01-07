from device_profile.command import MidiCommandBuilder
from rum.matchers import require_all, masked_status_eq, data1_eq, note_on, \
    channel_eq, note_off, data1_in_range


class LaunchkeyMk3(MidiCommandBuilder):
    """ MIDI Command structure for Novation LaunchkeyMk3. """

    # Reference:
    # https://www.kraftmusic.com/media/ownersmanual/Novation_Launchkey_Programmers_Reference_Manual.pdf
    _CMD_PREAMBLE = bytes([
        0x9F, 0x0C, 0x00,   # Exit DAW mode (defaults to drum layout
    ])

    SOLID_LED_STATUS_CMD = 0x99
    BLINK_LED_STATUS_CMD = 0x9B

    # Button constants
    # NOTE: You could very well enable DAW mode, switch buttons over to session
    # layout and use the 0x60-0x67, 0x70-0x77 ids.
    #
    # Novation seems to maintain a separate light state for different layouts
    # so you could technically use these as animation buffers or make changes
    # to different settings without needing to worry what mode is being
    # displayed. For our simple case, we will just use the drum layout which
    # is the default layout when the keyboard is first powered on.
    DRUM_PAD_IDS = [[0x28, 0x29, 0x2A, 0x2B, 0x30, 0x31, 0x32, 0x33],
                    [0x24, 0x25, 0x26, 0x27, 0x2C, 0x2D, 0x2E, 0x2F]]

    # Mapping of the channel index the buttons map to.
    CHANNEL_MAP = {pad_id: idx for idx, pad_id in
                   enumerate(DRUM_PAD_IDS[0] + DRUM_PAD_IDS[1])}

    DRUM_PAD_MIDI_CHANNEL = 9   # corresponds to channel 10

    # Various matchers
    IS_RECORD_BUTTON = require_all(masked_status_eq(0xB0), data1_eq(0x75))
    IS_PLAY_BUTTON = require_all(masked_status_eq(0xB0), data1_eq(0x73))
    IS_PAGE_UP_BUTTON = require_all(masked_status_eq(0xB0), data1_eq(0x68))
    IS_PAGE_DOWN_BUTTON = require_all(masked_status_eq(0xB0), data1_eq(0x69))
    IS_DRUM_PAD = require_all(channel_eq(DRUM_PAD_MIDI_CHANNEL),
                              data1_in_range(0x24, 0x33))

    @staticmethod
    def new_command():
        return LaunchkeyMk3()

    def __init__(self):
        super().__init__()
        self.param_lights_to_blink = []

    def blinking_light(self, *led_id_color_args):
        """ Set the lights on the device to blink a given color. """
        assert len(led_id_color_args) % 2 == 0
        for i in range(0, len(led_id_color_args), 2):
            self.param_lights_to_blink.append(
                (led_id_color_args[i], led_id_color_args[i + 1]))
        return self

    def build(self):
        # Start with the lights
        cmd = bytes()
        if (self.param_lights_to_turn_off
                or self.param_lights_to_turn_on
                or self.param_lights_to_set_colors
                or self.param_lights_to_blink):

            cmd += LaunchkeyMk3._CMD_PREAMBLE
            for led_id in self.param_lights_to_turn_off:
                cmd += bytes([LaunchkeyMk3.SOLID_LED_STATUS_CMD, led_id, 0x00])

            for led_id in self.param_lights_to_turn_on:
                cmd += bytes([LaunchkeyMk3.SOLID_LED_STATUS_CMD, led_id, 0x77])

            for led_id, led_value in self.param_lights_to_set_colors:
                cmd += bytes(
                    [LaunchkeyMk3.SOLID_LED_STATUS_CMD, led_id, led_value])

            for led_id, led_value in self.param_lights_to_blink:
                cmd += bytes(
                    [LaunchkeyMk3.BLINK_LED_STATUS_CMD, led_id, led_value])

        if self.param_display_updates:
            # No display on the Launchkey mini mk3
            pass
        return cmd
