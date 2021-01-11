from rum import lights, displays


class DeviceProfile:
    """ Interface for a device profile.

    A device profile specifies how to interface different components of a midi
    device with the framework API. Because there is the possibility of button
    inputs and output commands being on separate device ports, only an interface
    is provided and the remaining is left for the user to determine.
    """
    def __init__(self, is_daw_port, send_sysex_fn):
        self._is_daw_port = is_daw_port
        self._send_sysex_fn = send_sysex_fn

    def new_midi_command_builder(self):
        """ Return a new builder for constructing a midi command. """
        raise NotImplementedError()

    def new_color_toggle_light(self, led_id, off_value=0x00, on_value=0x7F):
        """ Return a new color toggle light instance representing the LED. """
        def set_light_color(value):
            builder: MidiCommandBuilder = self.new_midi_command_builder()
            cmd = builder.light_color(led_id, value).build(
                daw_mode=self._is_daw_port)
            self._send_sysex_fn(cmd)
        color_light = lights.ColorLight(update_fn=set_light_color,
                                        initial=off_value)
        return lights.ColorToggleLight(
            color_light, off_color=off_value, on_color=on_value)

    def new_toggle_light(self, led_id, daw_mode=True):
        """ Return a new toggle light instance representing the LED. """
        def light_on():
            builder: MidiCommandBuilder = self.new_midi_command_builder()
            cmd = builder.light_on(led_id).build(daw_mode=daw_mode)
            self._send_sysex_fn(cmd)

        def light_off():
            builder: MidiCommandBuilder = self.new_midi_command_builder()
            cmd = builder.light_off(led_id).build(daw_mode=daw_mode)
            self._send_sysex_fn(cmd)

        return lights.OnOffLight(on_fn=light_on,
                                 off_fn=light_off,
                                 initial=False)

    def new_display(self, daw_mode=True):
        """ Return a new display instance. """
        raise NotImplementedError()


class MidiCommandBuilder:
    """ Abstract base class for a builder for constructing midi commands.

    MidiCommandBuilder is used to create an efficient midi command byte string
    when needing to set multiple properties on a device at the same time. It's
    possible multiple light states need to be updated and if the device SYSEX
    format supports it, we can bundle the commands in a single midi command. If
    it's not supported, the same builder could just append a sequence of SYSEX
    commands to support this.
    """
    def __init__(self):
        # All build variables are prefixed with param_ so that it is easier
        # to lookup what parameters need to be built with
        # an IDE's code-completion capabilities.
        self.param_lights_to_set_colors = []
        self.param_lights_to_turn_on = []
        self.param_lights_to_turn_off = []
        self.param_display_updates = []

    def light_color(self, *light_value_args):
        """ Specify the light colors to update.

        This is specified by calling .light_color(id1, val1, id2, val2, ...).
        The input arguments are variable so multiple light ids and color values
        can be specified at once.
        """
        assert len(light_value_args) % 2 == 0
        for i in range(0, len(light_value_args), 2):
            self.param_lights_to_set_colors.append(
                (light_value_args[i], light_value_args[i+1])
            )
        return self

    def light_on(self, *light_ids):
        """ Specify the lights to turn on. """
        for i in range(len(light_ids)):
            self.param_lights_to_turn_on.append(light_ids[i])
        return self

    def light_off(self, *light_ids):
        """ Specify the lights to turn off. """
        for i in range(len(light_ids)):
            self.param_lights_to_turn_off.append(light_ids[i])
        return self

    def display(self, display_id, lines):
        """ Specify the lines to set for the given display_id. """
        self.param_display_updates.append((display_id, lines))
        return self

    def build(self, daw_mode=True):
        """ Returns a byte string representing the built midi command(s).

        This is device specific and must be implemented for each device.

        :param daw_mode: Set to true if building the command to be sent on
        DAW port. false otherwise
        """
        raise NotImplementedError()


