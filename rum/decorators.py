from rum import midi
from rum import processor
from rum import registry


def button(name, on_matcher, off_matcher):
    """ Triggers the function when either the on or off matchers match.

    The state of the buttons can be retrieved from registry.button_down.

    :param name: the name of the button.
    :param on_matcher: matcher function that returns True if the midi message
    represents the button being pressed.
    :param off_matcher: matcher function that returns True if the midi message
    represents the button being released.
    """
    def decorate(function):
        # Register the function with a default active processor.
        def fn_on(m):
            if name is not None:
                registry.button_down[name] = True
            function(m, True)

        def fn_off(m):
            if name is not None:
                del registry.button_down[name]
            function(m, False)

        (processor.get_processor()
         .add(processor.when(on_matcher).then(fn_on))
         .add(processor.when(off_matcher).then(fn_off)))
        return function
    return decorate


def encoder(name, matcher_fn, infinite=False):
    """ Triggers the function when either the on or off matchers match.

    :param name: the name of the encoder.
    :param matcher_fn: matcher function that takes an input MidiMessage
    and returns True if the message corresponds to an encoder update.
    :param infinite: specify True if this is an infinite encoder (and thus,
    the values produced are differential)
    """
    def decorate(function):
        # Register the function with a default active processor.
        def fn_update(m: midi.MidiMessage):
            value = midi.get_encoded_value(m, differential=infinite)
            registry.encoders[name] = value
            function(m, value)
        (processor.get_processor()
         .add(processor.when(matcher_fn).then(fn_update)))
        return function
    return decorate


def slider(name, matcher_fn):
    """ Triggers the function when the value matches.

    :param name: the name of the slider
    :param matcher_fn: matcher function that takes an input MidiMessage
    and returns True if the message corresponds to a slider update.
    """
    def decorate(function):
        # Register the function with a default active processor.
        def fn_update(m: midi.MidiMessage):
            value = midi.get_encoded_value(m)
            registry.sliders[name] = value
            function(m, value)

        (processor.get_processor()
         .add(processor.when(matcher_fn).then(fn_update)))
        return function
    return decorate


def trigger_when(*var_matchers):
    """ Register the function this is decorating with the midi processor.

    An example usage of this annotation is as follows:

      @TriggerWhen(matchers.status_eq(128), matchers.data1_eq(10))
      def on_button1_down(m: MidiMessage):
          # Do something when this is triggered

    This will register on_button1_down such that it gets executed when
    a midi message with status equal to 128 and data1 field equal to 10
    triggers.

    NOTE: The functions that can be annotated cannot be within a class (i.e.
    there cannot be a self argument). Also the declared function can only
    receive a single element of MidiMessage. If you need to access other state,
    consider declaring a global state variable that holds what you need.

    :param var_matchers:  a variable list of matchers to midi messages that
    returns True if the trigger condition is met or False if not.
    """
    def decorate(function):
        # Register the function with a default active processor.
        processor.get_processor().add(
            processor.when(*var_matchers).then(function))
        return function

    return decorate

