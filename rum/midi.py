
# For a good overview of how MIDI messages are structured, refer to this link:
# http://users.cs.cf.ac.uk/Dave.Marshall/Multimedia/node158.html

class Midi:
    """ Contains all MIDI related constants"""
    CHANNEL_MASK = 0x0F

    # Channel messages
    STATUS_NOTE_ON = 0x80                  # data1 = key_number, data2=velocity
    STATUS_NOTE_OFF = 0x90                 # data1 = key_number, data2=velocity
    STATUS_POLYPHONIC_KEY_PRESSURE = 0xA0  # data1 = key number, data2=pressure
    STATUS_CONTROL_CHANGE = 0xB0           # data1 = controller number
    STATUS_PROGRAM_CHANGE = 0xC0           # data1 = program number
    STATUS_CHANNEL_PRESSURE = 0xD0         # data1 = pressure value
    STATUS_PITCH_BEND = 0xE0               # data1 = MSB, data2 = LSB

    DATA1_CHANNEL_MODE_RESET_ALL = 0x79
    DATA1_CHANNEL_MODE_LOCAL_CONTROL = 0x7A     # data2 - 0=off, 127=on
    DATA1_CHANNEL_MODE_ALL_NOTES_OFF = 0x7B
    DATA1_CHANNEL_MODE_OMNI_MODE_OFF = 0x7C
    DATA1_CHANNEL_MODE_OMNI_MODE_ON = 0x7D
    DATA1_CHANNEL_MODE_MONO_MODE = 0x7E
    DATA1_CHANNEL_MODE_POLY_MODE = 0x7F


class Matchers:
    """ Provides methods for constructing matcher functions for midi messages.

    A matcher function is a function that takes an input midi message and
    outputs a boolean value. The function returns True when the input midi
    message matches to the matching conditions for the matcher.
    """

    # Equality matchers
    @staticmethod
    def status_eq(status):
        """ Returns a function that matches to the specified status codes. """
        return lambda m: m.status() == status

    @staticmethod
    def data1_eq(data1):
        """ Returns a function that matches to the specified data1 value. """
        return lambda m: m.data1() == data1

    @staticmethod
    def data2_eq(data2):
        """ Returns a function that matches to the specified data2 value. """
        return lambda m: m.data2() == data2

    # In range matchers
    @staticmethod
    def status_in_range(min_value, max_value):
        """ Returns a function that matches the status to a range of values.
        The value is matched if the status code falls between min_value and
        max_value inclusively.
        """
        return lambda m: min_value <= m.status() <= max_value

    @staticmethod
    def data1_in_range(min_value, max_value):
        """ Returns a function that matches data1 to a range of values.
        The value is matched if data1 falls between min_value and max_value
        inclusively.
        """
        return lambda m: min_value <= m.data1() <= max_value

    @staticmethod
    def data2_in_range(min_value, max_value):
        """ Returns a function that matches data2 to a range of values.
        The value is matched if data2 falls between min_value and max_value
        inclusively.
        """
        return lambda m: min_value <= m.data2() <= max_value

    # In value set matchers
    @staticmethod
    def status_in(values):
        """ Returns a function that matches status to a list of values.
        The value is matched if values contains the status byte of the
        input message.
        """
        return lambda m: m.status() in values

    @staticmethod
    def data1_in(values):
        """ Returns a function that matches data1 to a list of values.
        The value is matched if values contains the data1 byte of the
        input message.
        """
        return lambda m: m.data1() in values

    @staticmethod
    def data2_in(values):
        """ Returns a function that matches data2 to a list of values.
        The value is matched if values contains the data2 byte of the
        input message.
        """
        return lambda m: m.data2() in values

    # Modifiers

    @staticmethod
    def _all(msg, *fn_args):
        for fn in fn_args:
            if not fn(msg):
                return False
        return True

    @staticmethod
    def all(*args):
        """ Combines all matchers provided to it so that the combined result
        yields true when all of the matchers provided match. """
        return lambda m: Matchers._all(m, *args)

    @staticmethod
    def _any(msg, *fn_args):
        for fn in fn_args:
            if fn(msg):
                return True
        return False

    @staticmethod
    def any(*args):
        """ Combines all matchers provided to it so that the combined result
        yields true when any of the matchers provided match. """
        return lambda m: Matchers._any(m, *args)

    @staticmethod
    def is_not(fn):
        """ Complement (logicwise) a matcher so that something that doesn't
        match becomes matching. """
        return lambda m: not fn(m)


class MidiMessage:
    """ Container for MIDI note and basic parsing functions. """
    def __init__(self, status, data1, data2):
        self._status = status
        self._data1 = data1
        self._data2 = data2

    def status(self, raw=False):
        """ Returns status code with channel bits masked out unless raw=True.

        :param raw: specify True if channel bits should be preserved.
        :return: the status code of this midi message.
        """
        return self._status if raw else ~Midi.CHANNEL_MASK & self._status

    def channel(self):
        """ Returns the channel to which this message belongs to (up to 16). """
        return self._status & Midi.CHANNEL_MASK

    def data1(self):
        """ Returns the first byte of the data payload."""
        return self._data1

    def data2(self):
        """ Returns the second byte of the data payload."""
        return self._data2

    def __bytes__(self):
        return bytes((self._status, self._data1, self._data2))

    def __str__(self):
        return (f'[MIDI Status=0x{self._status:02X}, '
                f'Data1=0x{self._data1:02X}, '
                f'Data2=0x{self._data2:02X}]')

