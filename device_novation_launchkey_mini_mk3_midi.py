# name=RUM Novation Launchkey Mini Mk3 MIDI
# url=https://github.com/rjuang/rum
# receiveFrom=RUM Novation Launchkey Mini Mk3 DAW

from daw import flstudio
from device_profile.novation import LaunchkeyMk3
from rum import matchers, scheduling
from rum.midi import MidiMessage, Midi
from rum.matchers import masked_status_eq
from rum.processor import trigger_when
from rum.recorder import Recorder
from daw.flstudio import ChannelRack, register

DEBUG = True


def request_set_led(led_id, value):
    flstudio.Device.dispatch_message_to_other_scripts(
        LaunchkeyMk3.SOLID_LED_STATUS_CMD,
        led_id,
        value)


def request_blink_led(led_id, value):
    flstudio.Device.dispatch_message_to_other_scripts(
        LaunchkeyMk3.BLINK_LED_STATUS_CMD,
        led_id,
        value)


def play_note(msg: MidiMessage):
    ChannelRack.play_midi_note(
        msg.userdata['active_channelrack_index'],
        msg.data1,
        msg.data2)


class Device:
    """ Holds various states of the keyboard. """
    def __init__(self):
        self.profile = LaunchkeyMk3()
        # Notes that are currently pressed down.
        self.note_down = set()
        self.recorder = Recorder(scheduling.get_scheduler(),
                                 playback_fn=play_note)


_device = Device()


@trigger_when(LaunchkeyMk3.IS_RECORD_BUTTON)
def on_record_button_event(msg: MidiMessage):
    if matchers.IS_ON(msg):
        _device.note_down.add('record')
    else:
        _device.note_down.remove('record')
    msg.mark_handled()


@trigger_when(
    lambda _: 'record' in _device.note_down,        # Record button held
    lambda _: not _device.recorder.is_recording(),  # Not actively recording pad
    LaunchkeyMk3.IS_DRUM_PAD_DOWN                   # Is a drum pad press.
)
def start_recording_pad(msg: MidiMessage):
    request_blink_led(msg.data1, 0x05)
    _device.recorder.start_recording((msg.status, msg.data1))
    msg.mark_handled()


@trigger_when(LaunchkeyMk3.IS_RECORD_BUTTON, matchers.IS_ON)
def stop_recording_pad(msg: MidiMessage):
    if _device.recorder.is_recording():
        request_set_led(_device.recorder.get_recording_pattern_id()[1], 0)
        _device.recorder.stop_recording()
    msg.mark_handled()


@trigger_when(
    lambda _: 'record' not in _device.note_down,
    lambda _: not _device.recorder.is_recording(),
    LaunchkeyMk3.IS_DRUM_PAD_DOWN)
def recall_pad_pattern(msg: MidiMessage):
    if _device.recorder.play((msg.status, msg.data1)):
        msg.mark_handled()


@trigger_when(masked_status_eq(Midi.STATUS_NOTE_ON))
def on_note_down(msg: MidiMessage):
    if _device.recorder.get_recording_pattern_id() == (msg.status, msg.data1):
        # Don't send the key press we are recording
        return

    # Make sure to include info about the channel rack this is being played
    # from. NOTE: This doesn't work with locked down channels.
    msg.userdata['active_channelrack_index'] = ChannelRack.active_channel()
    _device.recorder.on_data_event(msg.timestamp_ms, msg)


@register
def OnInit():
    print('Loaded RUM Device Novation Launchkey Mini MK3')
    for row in LaunchkeyMk3.DRUM_PAD_IDS:
        for led_id in row:
            request_set_led(led_id, 0)


@register
def OnIdle():
    # This function needs to be declared and registered for the framework to
    # work properly.
    pass


@register
def OnMidiMsg(event):
    msg = flstudio.Midi.to_midi_message(event)
    if DEBUG:
        print(msg)
