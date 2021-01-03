# name=RUM - Novation Launchkey Mini Mk3 Looper
from rum.midi import MidiMessage, MidiProcessor, when, Matchers, when_all, \
    mark_handled
from rum.recorder import Recorder
from rum.scheduling import Scheduler
from daw.flstudio import ChannelRack

DEBUG = True

PADS_STATUS_BUTTON_DOWN = 0x99
PADS_STATUS_BUTTON_UP = 0x89


class Device:
    """ Holds various states of the keyboard. """
    def __init__(self):
        self._record_held = False
        self._scheduler = Scheduler()
        self._recorder = Recorder(self._scheduler, playback_fn=Device.play_note)

        def record_down(m): self._record_held = True
        def record_up(m): self._record_held = False
        def is_record_held(m): return self._record_held
        def is_record_not_held(m): return not self._record_held
        def not_recording(m): return not self._recorder.is_recording()
        def is_recording(m): return self._recorder.is_recording()
        def is_note_down(m: MidiMessage): return m.get_masked_status() == 0x90

        def start_recording(m):
            print(f'Recording {m.data1}')
            self._recorder.start_recording(m.data1)

        def stop_recording(m):
            print(f'Stop Recording')
            self._recorder.stop_recording()

        def play_pattern(m):
            print(f'Playback {m.data1}')
            return self._recorder.play(m.data1)

        self._processor = (
            MidiProcessor().add(
                when_all(is_recording,
                         Matchers.midi_eq(0xB0, 0x75, 0x7F))
                    .then(mark_handled, stop_recording),
                when(Matchers.midi_eq(0xB0, 0x75, 0x7F))
                    .then(mark_handled, record_down),
                when(Matchers.midi_eq(0xB0, 0x75, 0x00))
                    .then(mark_handled, record_up),
                when_all(is_record_held,
                         not_recording,
                         Matchers.status_eq(PADS_STATUS_BUTTON_DOWN))
                    .then(mark_handled, start_recording),
                when_all(is_record_not_held,
                         not_recording,
                         Matchers.status_eq(PADS_STATUS_BUTTON_DOWN),
                         play_pattern)
                    .then(mark_handled),
            )
        )

    def process(self, msg: MidiMessage):
        self._processor.process(msg)

    def idle(self):
        self._scheduler.idle()

    @staticmethod
    def play_note(msg: MidiMessage):
        ChannelRack.play_midi_note(
            msg.userdata['active_channel'],
            msg.data1,
            msg.data2)


device = Device()

def OnInit():
    print('Loaded RUM Library Debugger Tool')

def OnIdle():
    device.idle()

def OnMidiMsg(event):
    msg = MidiMessage(event.status, event.data1, event.data2)
    msg.userdata['active_channel'] = ChannelRack.active_channel()
    if DEBUG:
        print(msg)
    device.process(msg)
    if msg.is_handled():
        event.handled = True
