# name=RUM Novation Launchkey Mini Mk3 MIDI
# url=https://github.com/rjuang/rum
# receiveFrom=RUM Novation Launchkey Mini Mk3 DAW
import mixer

from daw import flstudio
from daw.flstudio import ChannelRack, register, Transport, MixerPanel
from device_profile.novation import LaunchkeyMk3
from panels.flstudio.channel import ChannelSelector
from rum import matchers, scheduling, midi, registry
from rum.matchers import midi_has, require_all
from rum.midi import MidiMessage, Midi
from rum.decorators import trigger_when, encoder, button
from rum.recorder import Recorder

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
        self.play_pad_press = None
        self.stop_pad_press = None
        self.last_loop = None
        self.current_loop_delay_ms = 0

    def is_pad_recording(self):
        return self.recorder.is_recording()

    def start_pad_recording(self, msg: MidiMessage):
        request_blink_led(msg.data1, 0x05)
        self.recorder.start_recording((msg.status, msg.data1))

    def stop_pad_recording(self):
        request_set_led(self.recorder.get_recording_pattern_id()[1], 0)
        self.recorder.stop_recording()

    def play_pad_pattern(self, msg: MidiMessage, loop=False):
        if loop:
            self.last_loop = (msg.status, msg.data1)
        return self.recorder.play((msg.status, msg.data1), loop=loop,
                                  loop_delay_ms=self.current_loop_delay_ms)


_device = Device()


@button('record',
        require_all(LaunchkeyMk3.IS_RECORD_BUTTON, matchers.IS_ON),
        require_all(LaunchkeyMk3.IS_RECORD_BUTTON, matchers.IS_OFF))
def on_record_button(msg: MidiMessage, pressed):
    if pressed:
        if _device.is_pad_recording():
            _device.stop_pad_recording()
    else:
        if not _device.is_pad_recording():
            Transport.record()
    msg.mark_handled()


@button('play',
        require_all(LaunchkeyMk3.IS_PLAY_BUTTON, matchers.IS_ON),
        require_all(LaunchkeyMk3.IS_PLAY_BUTTON, matchers.IS_OFF))
def on_play_button(msg: MidiMessage, pressed):
    if pressed:
        _device.play_pad_press = None
    else:
        if _device.play_pad_press is None:
            Transport.toggle_play()


@button('stop',
        require_all(LaunchkeyMk3.IS_PAGE_DOWN_BUTTON, matchers.IS_ON),
        require_all(LaunchkeyMk3.IS_PAGE_DOWN_BUTTON, matchers.IS_OFF))
def on_stop_button(msg: MidiMessage, pressed):
    if not pressed:
        if _device.recorder.is_recording():
            _device.stop_pad_recording()
        else:
            _device.recorder.stop_all()
        Transport.stop()


@button('>',
        require_all(LaunchkeyMk3.IS_PAGE_UP_BUTTON, matchers.IS_ON),
        require_all(LaunchkeyMk3.IS_PAGE_UP_BUTTON, matchers.IS_OFF))
def on_page_up_button(msg: MidiMessage, pressed):
    pass


def is_page_up_held(msg: MidiMessage):
    return registry.button_down['>']


@ChannelSelector([
    require_all(is_page_up_held, drum_pad_matcher)
    for drum_pad_matcher in LaunchkeyMk3.DRUM_PAD_DOWN_MATCHERS[0]])
def on_channel_selected(button_idx, channel_idx):
    for idx, pad_id in enumerate(LaunchkeyMk3.DRUM_PAD_IDS[0]):
        if idx == button_idx:
            request_set_led(pad_id, 0x10)
        else:
            request_set_led(pad_id, 0x0)


@trigger_when(LaunchkeyMk3.IS_DRUM_PAD)
def on_drum_pad(msg: MidiMessage):
    if msg.get_masked_status() == Midi.STATUS_NOTE_ON:
        if registry.button_down['record'] and not  _device.is_pad_recording():
            _device.start_pad_recording(msg)
            msg.mark_handled()
        elif (not registry.button_down['record'] and
              not _device.is_pad_recording()):
            loop = registry.button_down['play']
            if _device.play_pad_pattern(msg, loop=loop):
                _device.play_pad_press = (msg.status, msg.data1)
                msg.mark_handled()


@trigger_when(midi_has(status_range=(0x90, 0x9F)))
def on_note_down(msg: MidiMessage):
    if _device.recorder.get_recording_pattern_id() == (msg.status, msg.data1):
        # Don't send the key press we are recording
        return

    # Make sure to include info about the channel rack this is being played
    # from. NOTE: This doesn't work with locked down channels.
    msg.userdata['active_channelrack_index'] = ChannelRack.active_channel()
    _device.recorder.on_data_event(msg.timestamp_ms, msg)


# #############################################################################
#                             ENCODERS   1 - 8
# #############################################################################
@encoder('encoder1', LaunchkeyMk3.is_encoder(0))
def on_encoder1(msg: MidiMessage, value):
    # Set master volume to 0
    MixerPanel.set_track_volume(0, value)
    msg.mark_handled()


@encoder('encoder2', LaunchkeyMk3.is_encoder(1))
def on_encoder2(msg: MidiMessage, value):
    pass


@encoder('encoder3', LaunchkeyMk3.is_encoder(2))
def on_encoder3(msg: MidiMessage, value):
    pass


@encoder('encoder4', LaunchkeyMk3.is_encoder(3))
def on_encoder4(msg: MidiMessage, value):
    pass


@encoder('encoder5', LaunchkeyMk3.is_encoder(4))
def on_encoder5(msg: MidiMessage, value):
    pass


@encoder('encoder6', LaunchkeyMk3.is_encoder(5))
def on_encoder6(msg: MidiMessage, value):
    pass


@encoder('encoder7', LaunchkeyMk3.is_encoder(6))
def on_encoder7(msg: MidiMessage, value):
    pass


@encoder('encoder8', LaunchkeyMk3.is_encoder(7))
def on_encoder8(msg: MidiMessage, value):
    bpm = mixer.getCurrentTempo() / 1000
    quarter_beat_interval_ms = 15000 / bpm
    # Allow adjustment by quarter of a beat
    selection = [(i + 1) * quarter_beat_interval_ms for i in range(16)]
    idx = int(round((len(selection) - 1) * value))
    if _device.last_loop is not None:
        _device.recorder.set_loop_delay(_device.last_loop, selection[idx])
        _device.current_loop_delay_ms = selection[idx]


@register
def OnInit():
    print('Loaded RUM Device Novation Launchkey Mini MK3')


@register
def OnIdle():
    # This function needs to be declared and registered for the framework to
    # work properly.
    pass

@register
def OnRefresh(flags):
    if DEBUG:
        print(f'Refreshed with {flags}')

@register
def OnDoFullRefresh():
    if DEBUG:
        print(f'Do full refresh')



@register
def OnMidiMsg(event):
    msg = flstudio.Midi.to_midi_message(event)
    if DEBUG:
        print(msg)
