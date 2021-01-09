from rum import processor, autorefresh
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
        self._attached = True

    def attach(self):
        """ Put the panel in an attached state so messages are processed. """
        self._attached = True
        self.refresh()

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
        autorefresh.get_refresh_manager().add(self.refresh)

    def refresh(self, flags=autorefresh.FULL_REFRESH):
        """ Manually trigger a refresh (ignored if panel detached).

        :param flags specify a flag that is checked on to see if a refresh is
        needed required (defaults to full refresh so that refresh always
        called). The bits of the flag determines whether the refresh call
        will trigger an actual refresh. The meaning of the bits is DAW
        dependent.
        """
        if self._attached:
            self._refresh(flags)

    def _refresh(self, flags):
        """ Called when the outputs need to be re-drawn.

        :param flags specifies what components need to be refreshed. The
        value of the flags is DAW dependent.
        """
        raise NotImplementedError()

    def _process_message(self, msg: MidiMessage):
        """ Process the incoming message.

        This is a method any panel needs to implement. It needs to check
        whether the message matches any required conditions and executes any
        task associated with the panel.
        """
        raise NotImplementedError()

    def _decorate(self, fn):
        """ Decorate the provided function.

        When the class is constructed by a decorator, the function it is
        decorating will be passed to this method. This method will return the
        decorated function.

        :param fn: the function to decorate.
        :return the decorated function
        """
        raise NotImplementedError()

    def __call__(self, fn):
        # Enable this class to be used as a decorator by having it set the
        # trigger function as the function defined below the decorator
        # and automatically registering the panel.
        decorated_fn = self._decorate(fn)
        self.register()
        return decorated_fn
