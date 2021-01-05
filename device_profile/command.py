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

    def build(self):
        """ Returns a byte string representing the built midi command(s).

        This is device specific and must be implemented for each device.
        """
        raise NotImplementedError()


