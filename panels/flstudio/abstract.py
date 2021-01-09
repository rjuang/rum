from rum import processor
from rum.midi import MidiMessage


class Panel:
    """ Represents a function to control on the keyboard.

    A panel is a grouping of controls and displays/lights on the keyboard and
    serves to control one element of the DAW (e.g. volume, selecting channel,
    etc.). The panel serves to orchestrate the logic between matching a midi
    message to the correlated control, triggering the appropriate functions
    in the DAW, and outputting the appropriate display/lighting representative
    of the user's action.

    A panel can be in two states: attached or detached. When attached,
    the panel will process the message fed to it. When detached, it will
    ignore any messages being fed to it. This allows panels to share the same
    control inputs and be attached/detached depending on different modes.

    Finally, Panel classes are designed to be used as decorators. E.g.

    @SomePanel(arg1, arg2)
    def on_some_result(m: MidiMessage, in1, in2):
        pass

    """
    def __init__(self):
        self._attached = False

    def attach(self):
        """ Put the panel in an attached state so messages are processed. """
        self._attached = True

    def detach(self):
        """ Put the panel in a detached state so messages are dropped. """
        self._attached = False

    def process(self, msg: MidiMessage):
        """ Pass a message to the panel for processing. """
        if self._attached:
            self._process_message(msg)

    def register(self):
        """ Register this panel with the global processor. """
        processor.get_processor().add(self.process)

    def _process_message(self, msg: MidiMessage):
        raise NotImplementedError()

    def _init_decorator(self, fn):
        # Called when the decorator form of the class is used.
        raise NotImplementedError()

    def __call__(self, fn):
        # Enable this class to be used as a decorator by having it set the
        # trigger function as the function defined below the decorator
        # and automatically registering the panel.
        self._init_decorator(fn)
        self.register()
        return fn
