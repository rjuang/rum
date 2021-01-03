import time
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


class MidiMessage:
    """ Container for MIDI note and basic parsing functions. """
    def __init__(self, status, data1, data2, time_fn=None):
        if time_fn is None:
            time_fn = time.monotonic
        self.status = status
        self.data1 = data1
        self.data2 = data2

        self.handled = False
        self.timestamp_ms = int(time_fn() * 1000)
        # Include a field to annotate midi messages with custom user data.
        self.userdata = {}

    def get_masked_status(self):
        """ Returns status code with channel bits masked out. """
        return ~Midi.CHANNEL_MASK & self.status

    def get_channel(self):
        """ Returns the channel to which this message belongs to (up to 16). """
        return self.status & Midi.CHANNEL_MASK

    def mark_handled(self):
        """ Consume the midi event and mark the event as handled. """
        self.handled = True
        return self

    def __bytes__(self):
        return bytes((self.status, self.data1, self.data2))

    def __str__(self):
        return (f'[MIDI Status=0x{self.status:02X}, '
                f'Data1=0x{self.data1:02X}, '
                f'Data2=0x{self.data2:02X}]')

class When:
    """ Factory for converting a matcher function into a process function.

    A matcher function takes an input MidiMessage and returns a boolean
    specifying whether some conditional function on the input matches.

    A process function takes an input MidiMessage, and executes something
    based on the midi message.

    This class combines a matcher and processor so that it becomes an if-then
    processor function. To be fluent, use the

    e.g.
       process_fn = When(status_eq(128)).then(trigger_fn)
       ...
       process_fn(msg)   # Calls trigger_fn(msg) if msg.status == 128
    """
    def __init__(self, matcher_fn):
        self._matcher_fn = matcher_fn

    def then(self, *var_trigger_fn):
        """ Action to execute """
        def process_fn(msg):
            if self._matcher_fn(msg):
                for trigger_fn in var_trigger_fn:
                    trigger_fn(msg)

        return process_fn


class WhenAll(When):
    """ Similar to When but requires all input matchers to be True. """
    def __init__(self, *var_matcher_fns):
        super().__init__(Matchers.all(*var_matcher_fns))


class WhenAny(When):
    """ Similar to When but requires any input matchers to be True. """
    def __init__(self, *var_matcher_fns):
        super().__init__(Matchers.any(*var_matcher_fns))


# Convenience syntax. Allow lower-case function method call.
when = When
when_all = WhenAll
when_any = WhenAny


class Matchers:
    """ Provides methods for constructing matcher functions for midi messages.

    A matcher function is a function that takes an input midi message and
    outputs a boolean value. The function returns True when the input midi
    message matches to the matching conditions for the matcher.
    """
    @staticmethod
    def midi_eq(status, data1, data2):
        return lambda m: (m.status == status and
                          m.data1 == data1 and
                          m.data2 == data2)

    # Equality matchers
    @staticmethod
    def status_eq(status):
        """ Returns a function that matches to the specified status codes. """
        return lambda m: m.status == status

    @staticmethod
    def data1_eq(data1):
        """ Returns a function that matches to the specified data1 value. """
        return lambda m: m.data1 == data1

    @staticmethod
    def data2_eq(data2):
        """ Returns a function that matches to the specified data2 value. """
        return lambda m: m.data2 == data2

    # In range matchers
    @staticmethod
    def status_in_range(min_value, max_value):
        """ Returns a function that matches the status to a range of values.
        The value is matched if the status code falls between min_value and
        max_value inclusively.
        """
        return lambda m: min_value <= m.status <= max_value

    @staticmethod
    def data1_in_range(min_value, max_value):
        """ Returns a function that matches data1 to a range of values.
        The value is matched if data1 falls between min_value and max_value
        inclusively.
        """
        return lambda m: min_value <= m.data1 <= max_value

    @staticmethod
    def data2_in_range(min_value, max_value):
        """ Returns a function that matches data2 to a range of values.
        The value is matched if data2 falls between min_value and max_value
        inclusively.
        """
        return lambda m: min_value <= m.data2 <= max_value

    # In value set matchers
    @staticmethod
    def status_in(values):
        """ Returns a function that matches status to a list of values.
        The value is matched if values contains the status byte of the
        input message.
        """
        return lambda m: m.status in values

    @staticmethod
    def data1_in(values):
        """ Returns a function that matches data1 to a list of values.
        The value is matched if values contains the data1 byte of the
        input message.
        """
        return lambda m: m.data1 in values

    @staticmethod
    def data2_in(values):
        """ Returns a function that matches data2 to a list of values.
        The value is matched if values contains the data2 byte of the
        input message.
        """
        return lambda m: m.data2 in values

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


class MidiProcessor:
    def __init__(self):
        self._processors = []

    def add(self, *var_processor_fns):
        """ Add processor function to call when a midi message is processed. """
        for fn in var_processor_fns:
            self._processors.append(fn)
        return self

    def process(self, message: MidiMessage):
        """ Process a midi message. """
        for p in self._processors:
            p(message)
        return self


def mark_handled(msg: MidiMessage):
    """ Convenience function for marking a midi message handled. """
    msg.mark_handled()
