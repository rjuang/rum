""" All bindings to FL Studio dependent APIs will go here.

To simplify the programming concept, we break down the concept of FL Studio
into several independent components. These components can be controlled by
a dedicated device or device attached to controlling these device based on mode
changes.

The concepts are as follows:

- ChannelRack: This is the place users go to select the active instrument to
play, tweak the generated sound parameters (e.g. plugin params).
- MixerPanel: This is the place users go to tweak the volume/spatial levels of
different channels. This also includes mixer effects and routing information.
- TransportPanel: The transport panel is responsible for play/stop/record and
position of the song during recording/playback.
- PatternPanel: This is the place users go to switch to different pattern tracks
for recording. Users can also arrange/edit overall recorded patterns.

Buttons and controls can dynamically attach/detach from these individual
components.
"""

import channels
import device
import midi
import mixer
import transport

import rum.processor
from rum import scheduling, autorefresh

# Refresh flag constants that are one-hot encoded that represent refreshing
# different portions of the midi controller. These correspond to the flags in
# FL Studio (but with a different name).

REFRESH_MIXER_SELECTION = 1
REFRESH_MIXER_DISPLAY = 2
REFRESH_MIXER_CONTROLS = 4
REFRESH_REMOTE_LINKS = 16
REFRESH_FOCUSED_WINDOW = 32
REFRESH_PERFORMANCE = 64
REFRESH_CONTROLLER_LEDS = 256
REFRESH_REMOTE_LINKS = 512


class ChannelRack:
    """ Methods in FL Studio for controlling the channel rack. """
    @staticmethod
    def active_channel():
        """ Returns the first selected channel """
        return channels.selectedChannel()

    @staticmethod
    def num_channels():
        return channels.channelCount()

    @staticmethod
    def name(index):
        return channels.getChannelName(index)

    @staticmethod
    def set_active_channel(index):
        channels.selectOneChannel(index)

    @staticmethod
    def play_midi_note(channel, note, velocity):
        channels.midiNoteOn(channel, note, velocity)


class Midi:
    @staticmethod
    def to_midi_message(event: 'eventData'):
        """ Convert an FL Studio eventData midi message to MidiMessage. """
        return rum.midi.MidiMessage(event.status, event.data1, event.data2)


class MixerPanel:
    @staticmethod
    def set_track_volume(track_idx, volume):
        """ Sets the volume of the mixer track. """
        mixer.setTrackVolume(track_idx, volume)

    def get_current_tempo(self):
        """ Returns the current tempo. """
        return mixer.getCurrentTempo()


class Device:
    @staticmethod
    def send_sysex_message(byte_str):
        """ Send a midi SYSEX message to the linked output device. """
        return device.midiOutSysex(byte_str)

    @staticmethod
    def get_port_number():
        """ Fetches the MIDI port number assigned to this device. """
        return device.getPortNumber()

    @staticmethod
    def dispatch_message_to_other_scripts(status, data1, data2):
        """ Dispatches the midi note to all other scripts. """
        for i in range(device.dispatchReceiverCount()):
            msg = status + (data1 << 8) + (data2 << 16)
            device.dispatch(i, msg)


class Transport:
    @staticmethod
    def stop():
        transport.stop()

    @staticmethod
    def toggle_play():
        transport.globalTransport(midi.FPT_Play, midi.FPT_Play)

    @staticmethod
    def record():
        transport.record()


def register(function):
    """ Registers an FL Studio function with the RUM framework.

    Example usage:

    @register
    def OnMidiMsg( ... ):
        pass

    This will cause the corresponding method to be registered with the
    framework.
    """
    def init_function():
        # Force a full refresh when script attached.
        value = function()
        autorefresh.get_refresh_manager().refresh(autorefresh.FULL_REFRESH)
        return value

    def idle_function():
        scheduling.get_scheduler().idle()
        return function()

    def midi_msg_function(event_data):
        msg = Midi.to_midi_message(event_data)
        rum.processor.get_processor().process(msg)
        if msg.handled:
            event_data.handled = True
        return function(event_data)

    def refresh_function(flags):
        autorefresh.get_refresh_manager().refresh(flags)
        return function(flags)

    def full_refresh_function():
        autorefresh.get_refresh_manager().refresh(autorefresh.FULL_REFRESH)
        return function()

    if function.__name__ == 'OnIdle':
        return idle_function
    elif function.__name__ == 'OnMidiMsg':
        return midi_msg_function
    elif function.__name__ == 'OnRefresh':
        return refresh_function
    elif function.__name__ == 'OnInit':
        return init_function
    elif function.__name__ == 'OnDoFullRefresh':
        return full_refresh_function

    # Default to the undecorated function if we don't care
    return function
