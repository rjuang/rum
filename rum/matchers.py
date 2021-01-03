""" Classes and functions for constructing matcher functions. """

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
        super().__init__(require_all(*var_matcher_fns))


class WhenAny(When):
    """ Similar to When but requires any input matchers to be True. """
    def __init__(self, *var_matcher_fns):
        super().__init__(require_any(*var_matcher_fns))


# Convenience syntax. Allow lower-case function method call.
when = When
when_all = WhenAll
when_any = WhenAny


def midi_eq(status, data1, data2):
    return lambda m: (m.status == status and
                      m.data1 == data1 and
                      m.data2 == data2)


# Equality matchers
def status_eq(status):
    """ Returns a function that matches to the specified status codes. """
    return lambda m: m.status == status


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
