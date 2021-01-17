""" Components for controlling then channel rack. """
from daw import flstudio
from panels.abstract import Panel
from rum.midi import MidiMessage

# Last constructed channel selector. There should only ever by 1 channel
# selector.
_last_channel_selector = None


def get_channel_selector():
    """ Returns the last channel selector created. """
    return _last_channel_selector


class ChannelSelector(Panel):
    """ Selects the active channel based on a group of N matchers.

    Given a list of matchers, the channel selector will set the active channel
    based on the first successful matcher. Thus if the ith matcher in the list
    returns True (and all matchers before it don't match), then it will
    set the active channel in FL Studio to channel (i + base) where base
    defaults to 0 but can be changed.

    It will then trigger any output functions associated with it passing the
    message, the matcher index, and the channel index set.

    This class can be used as a function decorator to simplify any
    implementation.

    @ChannelSelector([matcher1, matcher2, ...])
    def on_channel_selected(m: MidiMessage, btn_index, channel_index):
        # ... any additional code to set lights/output dispays.
    """

    def __init__(self, button_matchers, attached=True, output_fn=None):
        """ Construct a ChannelSelector.

        :param button_matchers: a list of matchers (functions that take a
        MidiMessage and returns a boolean). Each matcher represents when a
        button is pressed/selected.
        :param attached: specifies whether the panel should be initially
        attached or not (default attached).
        :param output_fn: specifies the output function that should be called
        when a match is detected. For decorators, this should not be specified.
        The output function must be in the form:
           fn(m: MidiMessage, selected_index, channel_index)
        """
        super().__init__()
        self._matchers = button_matchers
        self._base_index = 0
        self._output_fn = output_fn
        self._attached = attached
        self._last_msg = None

        global _last_channel_selector
        _last_channel_selector = self

    def set_base_index(self, base_index):
        """ Specify the starting channel index the first matcher represents.

        For example, if base_index is 10, then if the first matcher provided
        matches, channel 10 is selected. If the second matcher provided
        matches, then channel 11 is selected, etc.
        """
        self._base_index = base_index

    def get_current_button_index(self):
        channel_idx = flstudio.ChannelRack.active_channel()
        return channel_idx - self._base_index

    def get_current_channel_index(self):
        return flstudio.ChannelRack.active_channel()

    def _process_message(self, msg: MidiMessage):
        for idx, match_fn in enumerate(self._matchers):
            if match_fn(msg):
                msg.mark_handled()
                channel_idx = self._base_index + idx
                if channel_idx >= flstudio.ChannelRack.num_channels():
                    return
                flstudio.ChannelRack.set_active_channel(channel_idx)
                # Note: We are always guaranteed an FL Studio refresh when
                # this propagates. Lighting and output will be handled on the
                # refresh call so that we don't double call.
                return

    def _decorate(self, fn):
        self._output_fn = fn
        if self._attached:
            self._refresh()
        return fn

    def _refresh(self, flags=0):
        if (flags & flstudio.REFRESH_FOCUSED_WINDOW) == 0:
            return
        channel_idx = flstudio.ChannelRack.active_channel()
        button_idx = channel_idx - self._base_index

        if button_idx < 0 or button_idx >= len(self._matchers):
            # Don't set an index if no mapping to a button
            button_idx = None
        if self._output_fn is not None:
            self._output_fn(button_idx, channel_idx)
