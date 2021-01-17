""" Contains classes for controlling LED lights on the device. """


class Light:
    """ Interface for a light source on the device. """
    def get(self): raise NotImplementedError()
    def set(self, value, force_update=False): raise NotImplementedError()

    def refresh(self):
        self.set(self.get(), force_update=True)

    def __bool__(self): raise NotImplementedError()


class ToggleLight(Light):
    """ Interface for a light source that can be toggled on the device. """
    def toggle(self, bool_value=None): raise NotImplementedError


class OnOffLight(ToggleLight):
    """ Controls a light on the device that can be toggled on/off. """
    def __init__(self, on_fn=None, off_fn=None, initial=False):
        self._on_fn = on_fn
        self._off_fn = off_fn
        self._status = initial
        self.set(initial)

    def __bool__(self):
        return self._status

    def get(self):
        """ Returns the state of the light. """
        return self._status

    def toggle(self, bool_value=None):
        """ Toggle the state of the light and returns updated state. """
        if bool_value is not None:
            self.set(bool_value)
        else:
            self.set(not self._status)
        return self._status

    def set(self, state, force_update=False):
        """ Sets the light on/off and sends the corresponding command.

        An update command is only issued if the state changed. To force an
        update command to be sent, set force_update to True.
        :param state:  the state to set the light to (True for ON and False for
        OFF).
        :param force_update: set to True to force an update command to be issued
        regardless of whether the light state changed.
        """
        dirty = self._status != state
        self._status = state

        if dirty or force_update:
            if state:
                if self._on_fn is not None:
                    self._on_fn()
            else:
                if self._off_fn is not None:
                    self._off_fn()

    def __repr__(self):
        return '[OnOffLight: {}]'.format("ON" if self._status else "OFF")


class ColorLight(Light):
    """ Controls a colored light source represented by a value.

    Colors can be represented as an RGB color with 24 bits of the 32-bit integer
    holding the red, green, blue channel information. Colors can also be
    specially coded by an enumeration like value where different values map to
    a preset color. This class does not distinguish between the two and simply
    provides an integer value that the user can set. The provided update
    function (which is device dependent) will provide this implementation.
    """
    def __init__(self, update_fn=None, initial=0):
        self._color = initial
        self._update_fn = update_fn

    def get(self):
        """ Returns the value of the light set. """
        return self._color

    def set(self, color, force_update=False):
        """ Sets the light color and sends the corresponding command.

        An update command is only issued if the state changed. To force an
        update command to be sent, set force_update to True.
        :param color:  the color value to set the light to
        :param force_update: set to True to force an update command to be issued
        regardless of whether the light color value changed.
        """
        dirty = self._color != color
        self._color = color
        if dirty or force_update:
            if self._update_fn is not None:
                self._update_fn(color)

    def __bool__(self):
        return self._color != 0

    def __repr__(self):
        return '[ColorLight: 0x{:02X}]'.format(self._color)


class ColorToggleLight(ToggleLight):
    """ Adapts a ColorLight so that it behaves as a toggle light. """

    def __init__(self, light: Light, off_color=0, on_color=0x7F):
        self._light = light
        self._off_color = off_color
        self._on_color = on_color

    def __bool__(self):
        return self._light.get() != self._off_color

    def toggle(self, bool_value=None):
        if bool_value is None:
            if self._light.get() == self._off_color:
                self._light.set(self._on_color)
            else:
                self._light.set(self._off_color)
        else:
            self._light.set(self._on_color if bool_value
                            else self._off_color)
        return self._light.get() != self._off_color

    def get(self):
        return self._light.get()

    def set(self, value, force_update=False):
        self._light.set(value, force_update=force_update)
        return self

    def set_off_color(self, off_color):
        self._off_color = off_color
        return self

    def set_on_color(self, on_color):
        self._on_color = on_color
        return self

    def __repr__(self):
        return ('[ColorToggleLight: {} | {}]'.format(
            "ON" if bool(self) else "OFF",
            self._light))
