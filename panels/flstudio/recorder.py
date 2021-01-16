import mixer
import rum.recorder

from daw.flstudio import ChannelRack
from panels import abstract
from rum import scheduling, midi
from rum.midi import MidiMessage, Midi


def _play_note(msg: MidiMessage):
    if msg.get_masked_status() == Midi.STATUS_NOTE_ON:
        ChannelRack.play_midi_note(
            msg.userdata['active_channelrack_index'],
            msg.data1,
            msg.data2)
    elif msg.get_masked_status() == Midi.STATUS_NOTE_OFF:
        ChannelRack.play_midi_note(
            msg.userdata['active_channelrack_index'],
            msg.data1,
            0)


_recorder = rum.recorder.Recorder(
    scheduling.get_scheduler(), playback_fn=_play_note)


def get_recorder():
    return _recorder


def get_pattern_id(msg: MidiMessage):
    return msg.status, msg.data1


# output_fn(pattern_id)
class RecordPattern(abstract.Panel):
    """ Register a midi event for triggering start of recording pattern.

    Example usage:
      @RecordPattern(midi_has(status_eq=0x90, data1_eq=0x30, data2_eq=0x7F))
      def on_record_start(pattern_id):
        # Turn on lights related to pattern_id or display.
        pass
    """
    def __init__(self, start_matcher, output_fn=None):
        super().__init__()
        self._start_matcher = start_matcher
        self._output_fn = output_fn

    def _refresh(self, flags):
        pattern_id = _recorder.get_recording_pattern_id()
        # Trigger a refresh for the recording pattern light if recording.
        if pattern_id is not None:
            self._output_fn(pattern_id)

    def _process_message(self, msg: MidiMessage):
        if _recorder.is_recording():
            # Do nothing if we are already recording
            return
        pattern_id = get_pattern_id(msg)
        if self._start_matcher(msg):
            _recorder.start_recording(pattern_id)
            if self._output_fn is not None:
                self._output_fn(pattern_id)
            msg.mark_handled()

    def _decorate(self, fn):
        self._output_fn = fn


class StopRecordPattern(abstract.Panel):
    def __init__(self, stop_matcher, output_fn=None):
        super().__init__()
        self._stop_matcher = stop_matcher
        self._output_fn = output_fn

    def _refresh(self, flags):
        pass

    def _process_message(self, msg: MidiMessage):
        if not _recorder.is_recording():
            # Already stopped. Nothing to do.
            return
        if self._stop_matcher(msg):
            pattern_id = _recorder.get_recording_pattern_id()
            print(f'Stop recording {pattern_id}')
            _recorder.stop_recording()
            if self._output_fn is not None:
                self._output_fn(pattern_id)

    def _decorate(self, fn):
        self._output_fn = fn


class PlayPattern(abstract.Panel):
    def __init__(self, play_matcher, output_fn=None):
        super().__init__()
        self._play_matcher = play_matcher
        self._output_fn = output_fn

    def _refresh(self, flags):
        pass

    def _process_message(self, msg: MidiMessage):
        if self._play_matcher(msg):
            pattern_id = get_pattern_id(msg)
            if _recorder.is_looping(pattern_id):
                _recorder.cancel_loop(pattern_id)
                self._output_fn(pattern_id, False)
                msg.mark_handled()
            elif _recorder.play(pattern_id):
                self._output_fn(pattern_id, True)
                msg.mark_handled()

    def _decorate(self, fn):
        self._output_fn = fn


class PlayLoop(abstract.Panel):
    def __init__(self, play_matcher, output_fn=None):
        super().__init__()
        self._play_matcher = play_matcher
        self._output_fn = output_fn

    def _refresh(self, flags):
        pass

    def _process_message(self, msg: MidiMessage):
        if self._play_matcher(msg):
            pattern_id = get_pattern_id(msg)
            if _recorder.is_looping(pattern_id):
                _recorder.cancel_loop(pattern_id)
                self._output_fn(pattern_id, False)
                msg.mark_handled()
            elif _recorder.play(pattern_id, loop=True):
                self._output_fn(pattern_id, True)
                msg.mark_handled()

    def _decorate(self, fn):
        self._output_fn = fn


class StopNow(abstract.Panel):
    def __init__(self, stop_matcher, output_fn=None):
        super().__init__()
        self._stop_matcher = stop_matcher
        self._output_fn = output_fn

    def _refresh(self, flags):
        pass

    def _process_message(self, msg: MidiMessage):
        if self._stop_matcher(msg):
            pattern_id = get_pattern_id(msg)
            _recorder.stop(pattern_id)
            self._output_fn(pattern_id)
            msg.mark_handled()

    def _decorate(self, fn):
        self._output_fn = fn


class StopAll(abstract.Panel):
    def __init__(self, stop_matcher, output_fn=None):
        super().__init__()
        self._stop_matcher = stop_matcher
        self._output_fn = output_fn

    def _refresh(self, flags):
        pass

    def _process_message(self, msg: MidiMessage):
        if self._stop_matcher(msg):
            _recorder.stop_recording()
            _recorder.stop_all()
            self._output_fn()
            msg.mark_handled()

    def _decorate(self, fn):
        self._output_fn = fn


class SetLoopDelay(abstract.Panel):
    def __init__(self, encoder_matcher,
                 infinite=False,
                 range=None,
                 step=0.5,
                 output_fn=None):
        super().__init__()

        if range is None:
            range = (0.0, 8.0)

        self._encoder_matcher = encoder_matcher
        self._output_fn = output_fn
        # Infinite encoders are incrmental encoders
        self._incremental = infinite
        self._range = range
        self._step = step

    def _refresh(self, flags):
        pass

    def _process_message(self, msg: MidiMessage):
        if self._encoder_matcher(msg):
            last_loop_id = _recorder.get_last_looping_pattern_id()
            if last_loop_id is None:
                return
            value = midi.get_encoded_value(msg, incremental=self._incremental)

            bpm = mixer.getCurrentTempo() / 1000
            step_ms = (60000 / bpm) * self._step
            num_steps = int((self._range[1] - self._range[0]) / float(
                self._step))

            # Allow adjustment by quarter of a beat
            selection = [i * step_ms + self._range[0]
                         for i in range(num_steps)]
            idx = int(round((len(selection) - 1) * value))
            loop_delay_ms = selection[idx]
            _recorder.set_loop_delay(last_loop_id, loop_delay_ms)

            self._output_fn(value, loop_delay_ms)
            msg.mark_handled()

    def _decorate(self, fn):
        self._output_fn = fn


class EventsForRecording(abstract.Panel):
    def __init__(self, filter_matcher, output_fn=None):
        super().__init__()
        self._filter_matcher = filter_matcher
        self._output_fn = output_fn

    def _refresh(self, flags):
        pass

    def _process_message(self, msg: MidiMessage):
        if not _recorder.is_recording:
            return

        if self._filter_matcher(msg):
            msg.userdata['active_channelrack_index'] = (
                ChannelRack.active_channel())
            _recorder.on_data_event(msg.timestamp_ms, msg)
            self._output_fn(msg)

    def _decorate(self, fn):
        self._output_fn = fn