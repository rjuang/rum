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
        return ('[MIDI Status=0x{:02X}, '.format(self.status) +
                'Data1=0x{:02X}, '.format(self.data1) +
                'Data2=0x{:02X}]'.format(self.data2))


def mark_handled(msg: MidiMessage):
    """ Convenience function for marking a midi message as handled. """
    msg.mark_handled()


def get_encoded_value(msg: MidiMessage, max_val=0x7F, range=(0.0, 1.0),
                      incremental=False):
    """  Retrieve the encoder value (data2) and remap result to a given range.

    This function assumes the msg provided is associated with an encoder. It
    does not check the message for validity and assumes the caller has already
    done so.

    :param msg: the msg to retrieve the encoder value from
    :param range: the range to map the values to inclusive (default (0.0, 1.0)
    :param incremental: set to True if the encoded value represents an
     incremental value (+/- delta value)
    :return: the encoder value in the mapped range as a float.
    """
    if incremental:
        sign = 1
        if 0b1000000 & msg.data2 > 0:
            sign = -1
        return float(sign * (msg.data2 & 0b111111)) / max_val * (range[1] -
                                                                 range[0])
    else:
        return msg.data2 / float(max_val) * float(range[1] - range[0]) + float(
        range[0])

