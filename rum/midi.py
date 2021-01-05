import time
# For a good overview of how MIDI messages are structured, refer to this link:
# http://users.cs.cf.ac.uk/Dave.Marshall/Multimedia/node158.html

class Midi:
    """ Contains all MIDI related constants"""
    CHANNEL_MASK = 0x0F

    # Channel messages
    STATUS_NOTE_ON = 0x90                  # data1 = key_number, data2=velocity
    STATUS_NOTE_OFF = 0x80                 # data1 = key_number, data2=velocity
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


def mark_handled(msg: MidiMessage):
    """ Convenience function for marking a midi message as handled. """
    msg.mark_handled()


class MidiProcessor:
    """ Processor whose sole function is to dispatch midi messages.

    MidiProcessor is a convenience structure that receives a single midi message
    and dispatches it to multiple end points. These dispatch functions can
    have built-in conditions that drop or transmit the message to its end point.
    """
    def __init__(self):
        self._processors = []

    def add(self, *var_processor_fns):
        """ Add processor function to trigger when a midi message is processed.

        This method accepts a variable number of arguments. The functions are
        triggered in the order they are added and provided. Each function
        will be passed a single argument of type MidiMessage. This message is
        mutable and changes to it will be propagated to the later processing
        functions. The MidiMessage can be marked handled by modifying the
        handled field. This prevents further processing by FL Studio (e.g.
        sound generation).

        :param var_processor_fns: a variable list of processor functions to
        call when a midi message is input. A processor function takes a single
        input argument of type MidiMessage. The functions are called in the
        order they are provided and added.
        :return: this instance for further operation chaining
        """
        for fn in var_processor_fns:
            self._processors.append(fn)
        return self

    def process(self, message: MidiMessage):
        """ Process midi message by sending it to all processor functions. """
        for p in self._processors:
            p(message)
        return self