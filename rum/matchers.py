""" Classes and functions for constructing matcher functions. """
from rum.midi import Midi


def midi_has(status=None, data1=None, data2=None,
             status_range=None, data1_range=None, data2_range=None,
             status_in=None, data1_in=None, data2_in=None):
    """ Returns a function that matches to messages with the provided args.

    If None is specified, then that argument is not matched against. If one
    of the *_range keywords is specified, then the requirement is for that
    data field of the midi message to fall within the range specified inclusive.
    If one of the *_in keywords is specified, then the requirement is for
    that data field of the midi message to be one of the elements of the
    list/tuple specified.
    """
    return lambda m: ((status is None or m.status == status) and
                      (data1 is None or m.data1 == data1) and
                      (data2 is None or m.data2 == data2) and
                      (status_range is None or
                       status_range[0] <= m.status <= status_range[1]) and
                      (data1_range is None or
                       data1_range[0] <= m.data1 <= data1_range[1]) and
                      (data2_range is None or
                       data2_range[0] <= m.data2 <= data2_range[1]) and
                      (status_in is None or m.status in status_in) and
                      (data1_in is None or m.data1 in data1_in) and
                      (data2_in is None or m.data2 in data2_in))


def note_on():
    """ Returns a function that matches to messages with note on. """
    return lambda msg: msg.get_masked_status() == Midi.STATUS_NOTE_ON


def note_off():
    """ Returns a function that matches to messages with note off. """
    return lambda msg: msg.get_masked_status() == Midi.STATUS_NOTE_OFF


def channel_eq(channel):
    """ Returns a function that matches to messages from the midi channel. """
    return lambda msg: msg.get_channel() == channel


# Equality matchers
def status_eq(status):
    """ Returns a function that matches to the specified status codes. """
    return lambda m: m.status == status


def masked_status_eq(masked_status):
    """ Returns a function that matches to the masked status. """
    return lambda m: m.get_masked_status() == masked_status


def data1_eq(data1):
    """ Returns a function that matches to the specified data1 value. """
    return lambda m: m.data1 == data1


def data2_eq(data2):
    """ Returns a function that matches to the specified data2 value. """
    return lambda m: m.data2 == data2


# In range matchers
def status_in_range(min_value, max_value):
    """ Returns a function that matches the status to a range of values.
    The value is matched if the status code falls between min_value and
    max_value inclusively.
    """
    return lambda m: min_value <= m.status <= max_value


def data1_in_range(min_value, max_value):
    """ Returns a function that matches data1 to a range of values.
    The value is matched if data1 falls between min_value and max_value
    inclusively.
    """
    return lambda m: min_value <= m.data1 <= max_value


def data2_in_range(min_value, max_value):
    """ Returns a function that matches data2 to a range of values.
    The value is matched if data2 falls between min_value and max_value
    inclusively.
    """
    return lambda m: min_value <= m.data2 <= max_value


# In value set matchers
def status_in(values):
    """ Returns a function that matches status to a list of values.
    The value is matched if values contains the status byte of the
    input message.
    """
    return lambda m: m.status in values


def data1_in(values):
    """ Returns a function that matches data1 to a list of values.
    The value is matched if values contains the data1 byte of the
    input message.
    """
    return lambda m: m.data1 in values


def data2_in(values):
    """ Returns a function that matches data2 to a list of values.
    The value is matched if values contains the data2 byte of the
    input message.
    """
    return lambda m: m.data2 in values


# For buttons:
# Matches when a control change message or command message represents a toggle
# button and has value of ON.
IS_ON = data2_eq(0x7F)
# Matches when a control change message or command message represents a toggle
# button and has value of OFF.
IS_OFF = data2_eq(0x00)


# Modifiers
def _all(msg, *fn_args):
    for fn in fn_args:
        if not fn(msg):
            return False
    return True


def require_all(*args):
    """ Combines all matchers provided to it so that the combined result
    yields true when all of the matchers provided match. """
    return lambda m: _all(m, *args)


def _any(msg, *fn_args):
    for fn in fn_args:
        if fn(msg):
            return True
    return False


def require_any(*args):
    """ Combines all matchers provided to it so that the combined result
    yields true when any of the matchers provided match. """
    return lambda m: _any(m, *args)


def is_not(fn):
    """ Complement (logicwise) a matcher so that something that doesn't
    match becomes matching. """
    return lambda m: not fn(m)
