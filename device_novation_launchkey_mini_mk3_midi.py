# name=RUM Novation Launchkey Mini Mk3 MIDI
# url=https://github.com/rjuang/rum
# receiveFrom=RUM Novation Launchkey Mini Mk3 DAW

from daw import flstudio
from device_profile.novation import LaunchkeyMk3
from rum import matchers
from rum.midi import MidiMessage, mark_handled, MidiProcessor, Midi
from rum.matchers import when
from rum.recorder import Recorder
from rum.scheduling import Scheduler
from daw.flstudio import ChannelRack

DEBUG = True


class Device:
    """ Holds various states of the keyboard. """
    def __init__(self):
        self._profile = LaunchkeyMk3()
        self._record_held = False
        self._scheduler = Scheduler()
        self._recorder = Recorder(self._scheduler, playback_fn=Device.play_note)
        self._recording_key = None

        def record_down(_): self._record_held = True
        def record_up(_): self._record_held = False
        def is_record_held(_): return self._record_held
        def is_record_not_held(_): return not self._record_held
        def not_recording_pad(_): return not self._recorder.is_recording()
        def is_note_down(m: MidiMessage): return m.get_masked_status() == 0x90

        def blink_led(led_id, value):
            flstudio.Device.dispatch_message_to_other_scripts(
                LaunchkeyMk3.BLINK_LED_STATUS_CMD,
                led_id,
                value)

        def start_recording_pad(m: MidiMessage):
            blink_led(m.data1, 0x05)
            self._recorder.start_recording((m.status, m.data1))
            self._recording_key = (m.status, m.data1)

        def stop_any_pad_recording(m : MidiMessage):
            if self._recording_key is not None:
                self.set_led(self._recording_key[1], 0x00)
            if self._recorder.is_recording():
                self._recorder.stop_recording()

        def mark_handled_if_play_pattern(m: MidiMessage):
            if self._recorder.play((m.status, m.data1)):
                m.mark_handled()

        def send_to_recorder(m: MidiMessage):
            # Don't send the key press we are recording
            if self._recording_key != (m.status, m.data1):
                self._recorder.on_data_event(m.timestamp_ms, m)

        self._processor = (
            MidiProcessor().add(
                when(LaunchkeyMk3.IS_RECORD_BUTTON, matchers.IS_ON)
                .then(mark_handled,
                      record_down,
                      stop_any_pad_recording),

                when(LaunchkeyMk3.IS_RECORD_BUTTON, matchers.IS_OFF)
                .then(mark_handled, record_up),

                when(is_record_held,
                     not_recording_pad,
                     LaunchkeyMk3.IS_DRUM_PAD_DOWN)
                .then(mark_handled, start_recording_pad),

                # If drum pad button press when not recording and record button
                # not beind held, try to play the pattern associated with the
                # note
                when(is_record_not_held,
                     not_recording_pad,
                     LaunchkeyMk3.IS_DRUM_PAD_DOWN)
                .then(mark_handled_if_play_pattern),

                when(LaunchkeyMk3.IS_DRUM_PAD_UP)
                .then(mark_handled),

                # When any note down event detected, send note to recorder
                when(is_note_down).then(send_to_recorder)
            )
        )

    def set_led(self, led_id, value):
        flstudio.Device.dispatch_message_to_other_scripts(
            LaunchkeyMk3.SOLID_LED_STATUS_CMD,
            led_id,
            value)

    def process(self, msg: MidiMessage):
        self._processor.process(msg)

    def idle(self):
        self._scheduler.idle()

    @staticmethod
    def play_note(msg: MidiMessage):
        ChannelRack.play_midi_note(
            msg.userdata['active_channelrack_index'],
            msg.data1,
            msg.data2)


_device = Device()


def OnInit():
    print('Loaded RUM Device Novation Launchkey Mini MK3')
    for row in LaunchkeyMk3.DRUM_PAD_IDS:
        for led_id in row:
            _device.set_led(led_id, 0)


def OnIdle():
    _device.idle()


def OnMidiMsg(event):
    msg = MidiMessage(event.status, event.data1, event.data2)
    msg.userdata['active_channelrack_index'] = ChannelRack.active_channel()
    if DEBUG:
        print(msg)
    _device.process(msg)
    if msg.handled:
        event.handled = True
