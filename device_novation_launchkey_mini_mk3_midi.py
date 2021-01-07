# name=RUM Novation Launchkey Mini Mk3 MIDI
# url=https://github.com/rjuang/rum
# receiveFrom=RUM Novation Launchkey Mini Mk3 DAW
import mixer

from daw import flstudio
from daw.flstudio import ChannelRack, register, Transport, MixerPanel
from device_profile.novation import LaunchkeyMk3
from rum import matchers, scheduling, midi
from rum.matchers import midi_has
from rum.midi import MidiMessage, Midi
from rum.processor import trigger_when
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

    def mark_pressed(self, note):
        self.note_down.add(note)

    def mark_released(self, note):
        self.note_down.remove(note)

    def is_pressed(self, note):
        return note in self.note_down

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


@trigger_when(LaunchkeyMk3.IS_RECORD_BUTTON)
def on_record_button(msg: MidiMessage):
    if matchers.IS_ON(msg):
        _device.mark_pressed('record')
        if _device.is_pad_recording():
            _device.stop_pad_recording()
    else:
        _device.mark_released('record')
        if not _device.is_pad_recording():
            Transport.record()
    msg.mark_handled()


@trigger_when(LaunchkeyMk3.IS_PLAY_BUTTON)
def on_play_button(msg: MidiMessage):
    if matchers.IS_ON(msg):
        _device.mark_pressed('play')
        _device.play_pad_press = None
    else:
        _device.mark_released('play')
        if _device.play_pad_press is None:
            Transport.toggle_play()


@trigger_when(LaunchkeyMk3.IS_PAGE_DOWN_BUTTON)
def on_stop_button(msg: MidiMessage):
    if matchers.IS_ON(msg):
        _device.mark_pressed('stop')
    else:
        _device.mark_released('stop')
        if _device.recorder.is_recording():
            _device.stop_pad_recording()
        else:
            _device.recorder.stop_all()
        Transport.stop()


@trigger_when(LaunchkeyMk3.IS_PAGE_UP_BUTTON)
def on_page_up_button(msg: MidiMessage):
    if matchers.IS_ON(msg):
        _device.mark_pressed('>')
    else:
        _device.mark_released('>')


@trigger_when(LaunchkeyMk3.IS_DRUM_PAD)
def on_drum_pad(msg: MidiMessage):
    if msg.get_masked_status() == Midi.STATUS_NOTE_ON:
        if _device.is_pressed('record') and not _device.is_pad_recording():
            _device.start_pad_recording(msg)
            msg.mark_handled()
        elif _device.is_pressed('>'):
            chan = LaunchkeyMk3.CHANNEL_MAP[msg.data1]
            if chan < ChannelRack.num_channels():
                ChannelRack.set_active_channel(chan)
            msg.mark_handled()
        elif (not _device.is_pressed('record') and
              not _device.is_pad_recording()):
            loop = _device.is_pressed('play')
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


@trigger_when(midi_has(status_range=(0xB0, 0xB9),
                       data1_in=LaunchkeyMk3.ENCODER_IDS))
def on_encoder_turned(msg: MidiMessage):
    chan = msg.get_channel()
    encoder_idx = LaunchkeyMk3.ENCODER_MAP[msg.data1]
    value = midi.get_encoder_value(msg)

    if encoder_idx == 0:
        MixerPanel.set_track_volume(encoder_idx, value)
    elif encoder_idx == 7:
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
