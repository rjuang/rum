# name=RUM Novation Launchkey Mini Mk3 MIDI
# url=https://github.com/rjuang/rum
# receiveFrom=RUM Novation Launchkey Mini Mk3 DAW

from daw import flstudio
from daw.flstudio import register, Transport, MixerPanel
from device_profile.novation.launchkey.mini_mk3 import \
    MiniMk3
from panels.flstudio import recorder, lights, channel
from panels.flstudio.channel import ChannelSelector
from panels.flstudio.lights import LightPanel
from rum import matchers, registry
from rum.decorators import encoder, button
from rum.matchers import midi_has, require_all, is_not
from rum.midi import MidiMessage

DEBUG = True

RECORDING_COLOR = (True, 0x05)
IDLE_CHANNEL_SELECTED_COLOR = (False, 0x10)
IDLE_PLAYABLE_COLOR = (False, 0x5C)
IDLE_NOT_PLAYABLE_COLOR = (False, 0x00)
PLAY_LOOP_COLOR = (False, 0x0D)

# Novation supports a special blink command. As such, the "color value"
# will be a pair (is_blinking, color). Colors can be made to blink by setting
# the is_blinking value to True.
def request_set_led(led_id, value: (bool, int)):
    is_blinking, led_color = value
    led_cmd = (MiniMk3.BLINK_LED_STATUS_CMD if is_blinking
               else MiniMk3.SOLID_LED_STATUS_CMD)
    flstudio.Device.dispatch_message_to_other_scripts(
        led_cmd,
        led_id,
        led_color)


def refresh_lights():
    # Update the off pattern colors
    for pattern_id in recorder.get_recorder().get_patterns():
        lights.get_light(pattern_id[1]).set_off_color(IDLE_PLAYABLE_COLOR)

    lights.get_panel('drumpad_row1').toggle_all(False)
    lights.get_panel('drumpad_row2').toggle_all(False)

    # Update the channel selector
    button_idx = channel.get_channel_selector().get_current_button_index()
    if 0 <= button_idx < len(MiniMk3.DRUM_PAD_IDS[0]):
        light = lights.get_panel('drumpad_row1')[button_idx]
        light.set_on_color(IDLE_CHANNEL_SELECTED_COLOR)
        light.toggle(True)

    # Update any recording pattern
    for pattern_id in recorder.get_recorder().get_looping_patterns():
        light = lights.get_light(pattern_id[1])
        light.set_on_color(PLAY_LOOP_COLOR)
        light.toggle(True)

    # Update any patterns currently being recorded
    pattern_id = recorder.get_recorder().get_recording_pattern_id()
    if pattern_id is not None:
        light = lights.get_light(pattern_id[1])
        light.set_on_color(RECORDING_COLOR)
        light.toggle(True)


@LightPanel('drumpad_row1',
            MiniMk3.DRUM_PAD_IDS[0],
            light_fn=request_set_led,
            initial=(False, 0),
            off_color=(False, 0),
            on_color=(False, 0x73))
def on_update_drumpad1_lights(led_id, value):
    request_set_led(led_id, value)


@LightPanel('drumpad_row2',
            MiniMk3.DRUM_PAD_IDS[1],
            light_fn=request_set_led,
            initial=(False, 0),
            off_color=(False, 0),
            on_color=(False, 0x73))
def on_update_drumpad2_lights(led_id, value):
    request_set_led(led_id, value)


class Device:
    """ Holds various states of the keyboard. """
    def __init__(self):
        # Notes that are currently pressed down.
        self.recorder = recorder.get_recorder()
        self.play_pad_press = None
        self.stop_record_issued = False
        self.stop_command_issued = False


_device = Device()


def is_record_held(msg: MidiMessage):
    return registry.button_down['record']


def is_pad_recording(msg: MidiMessage):
    return recorder.get_recorder().is_recording()


@recorder.RecordPattern(require_all(is_record_held, MiniMk3.IS_DRUM_PAD))
def on_start_recording_pad(pattern_id):
    light = lights.get_light(pattern_id[1])
    light.set_on_color(RECORDING_COLOR)
    light.toggle(bool_value=True)


@recorder.StopRecordPattern(
    require_all(is_pad_recording,
                MiniMk3.IS_RECORD_BUTTON,
                matchers.IS_ON))
def on_stop_recording_pad(pattern_id):
    _device.stop_record_issued = True
    light = lights.get_light(pattern_id[1])
    if recorder.get_recorder().has_pattern(pattern_id):
        light.set_off_color(IDLE_PLAYABLE_COLOR)
    else:
        light.set_off_color(IDLE_NOT_PLAYABLE_COLOR)
    light.toggle(bool_value=False)


@recorder.StopRecordPattern(
    require_all(is_pad_recording,
                MiniMk3.IS_PAGE_DOWN_BUTTON,
                matchers.IS_ON))
def on_stop_recording_pad_stop(pattern_id):
    _device.stop_record_issued = True
    light = lights.get_light(pattern_id[1])
    if recorder.get_recorder().has_pattern(pattern_id[1]):
        light.set_off_color(IDLE_PLAYABLE_COLOR)
    else:
        light.set_off_color(IDLE_NOT_PLAYABLE_COLOR)
    light.toggle(bool_value=False)


@button('record',
        require_all(MiniMk3.IS_RECORD_BUTTON, matchers.IS_ON),
        require_all(MiniMk3.IS_RECORD_BUTTON, matchers.IS_OFF))
def on_record_button(msg: MidiMessage, pressed):
    if not pressed:
        if not _device.stop_record_issued and not is_pad_recording(msg):
            Transport.record()
        _device.stop_record_issued = False
    msg.mark_handled()


@button('play',
        require_all(MiniMk3.IS_PLAY_BUTTON, matchers.IS_ON),
        require_all(MiniMk3.IS_PLAY_BUTTON, matchers.IS_OFF))
def on_play_button(msg: MidiMessage, pressed):
    if pressed:
        _device.play_pad_press = None
    else:
        if _device.play_pad_press is None:
            Transport.toggle_play()


def is_play_button_held(msg: MidiMessage):
    return registry.button_down['play']


@button('stop',
        require_all(MiniMk3.IS_PAGE_DOWN_BUTTON, matchers.IS_ON),
        require_all(MiniMk3.IS_PAGE_DOWN_BUTTON, matchers.IS_OFF))
def on_stop_button(msg: MidiMessage, pressed):
    if pressed:
        _device.stop_command_issued = False
    elif not _device.stop_command_issued:
        Transport.stop()


def is_stop_button_held(msg: MidiMessage):
    return registry.button_down['stop']


@recorder.StopNow(require_all(
    is_stop_button_held,
    MiniMk3.IS_DRUM_PAD,
))
def on_stop_playing_pad_now(pattern_id):
    _device.stop_command_issued = True
    lights.get_light(pattern_id[1]).toggle(False)


@button('>',
        require_all(MiniMk3.IS_PAGE_UP_BUTTON, matchers.IS_ON),
        require_all(MiniMk3.IS_PAGE_UP_BUTTON, matchers.IS_OFF))
def on_page_up_button(msg: MidiMessage, pressed):
    pass


def is_page_up_held(msg: MidiMessage):
    return registry.button_down['>']


@ChannelSelector([
    require_all(is_page_up_held, drum_pad_matcher)
    for drum_pad_matcher in MiniMk3.DRUM_PAD_DOWN_MATCHERS[0]])
def on_channel_selected(button_idx, channel_idx):
    refresh_lights()


@recorder.PlayPattern(require_all(
    MiniMk3.IS_DRUM_PAD,
    is_not(is_stop_button_held),
    is_not(is_play_button_held),
    is_not(is_page_up_held),
    is_not(is_record_held),
    is_not(is_pad_recording)
))
def on_play_pattern(pattern_id, is_start):
    pass


@recorder.PlayLoop(require_all(
    MiniMk3.IS_DRUM_PAD,
    is_play_button_held,
    is_not(is_record_held),
    is_not(is_stop_button_held),
    is_not(is_pad_recording)))
def on_toggle_play_loop(pattern_id, is_start):
    _device.play_pad_press = pattern_id
    if is_start:
        light = lights.get_light(pattern_id[1])
        light.set_on_color(PLAY_LOOP_COLOR)
    light.toggle(is_start)


def matches_recording_pattern_id(msg: MidiMessage):
    pattern_id = _device.recorder.get_recording_pattern_id()
    if pattern_id is None:
        return False
    return MiniMk3.IS_DRUM_PAD(msg) and pattern_id[1] == msg.data1


@recorder.EventsForRecording(require_all(
    midi_has(status_range=(0x80, 0x9F)),
    is_not(matches_recording_pattern_id)))
def on_note_event(msg: MidiMessage):
    pass


@recorder.StopAll(
    require_all(
        MiniMk3.IS_PAGE_DOWN_BUTTON,
        matchers.IS_OFF,
        lambda _: not _device.stop_command_issued
    ))
def on_stop_all():
    refresh_lights()


# #############################################################################
#                             ENCODERS   1 - 8
# #############################################################################
@encoder('encoder1', MiniMk3.is_encoder(0))
def on_encoder1(msg: MidiMessage, value):
    # Set master volume to 0
    MixerPanel.set_track_volume(0, value)
    msg.mark_handled()


@encoder('encoder2', MiniMk3.is_encoder(1))
def on_encoder2(msg: MidiMessage, value):
    pass

@encoder('encoder3', MiniMk3.is_encoder(2))
def on_encoder3(msg: MidiMessage, value):
    pass


@encoder('encoder4', MiniMk3.is_encoder(3))
def on_encoder4(msg: MidiMessage, value):
    pass


@encoder('encoder5', MiniMk3.is_encoder(4))
def on_encoder5(msg: MidiMessage, value):
    pass


@encoder('encoder6', MiniMk3.is_encoder(5))
def on_encoder6(msg: MidiMessage, value):
    pass


@encoder('encoder7', MiniMk3.is_encoder(6))
def on_encoder7(msg: MidiMessage, value):
    pass


@recorder.SetLoopDelay(MiniMk3.is_encoder(7))
def on_set_loop_delay(value, loop_delay_ms):
    selected = int(value * (len(MiniMk3.DRUM_PAD_IDS[1]) - 1))
    for i in range(len(MiniMk3.DRUM_PAD_IDS[1])):
        request_set_led(MiniMk3.DRUM_PAD_IDS[1][i],
                        (False, 0x39 if i == selected else 0))

@register
def OnInit():
    print('Loaded RUM Device Novation Launchkey Mini MK3')
    lights.get_panel('drumpad_row1').toggle_all(False)
    lights.get_panel('drumpad_row2').toggle_all(False)


@register
def OnIdle():
    # This function needs to be declared and registered for the framework to
    # work properly.
    pass


@register
def OnRefresh(flags):
    if DEBUG:
        print('Refreshed with {}'.format(flags))


@register
def OnDoFullRefresh():
    if DEBUG:
        print('Do full refresh')


@register
def OnMidiMsg(event):
    msg = flstudio.Midi.to_midi_message(event)
    if DEBUG:
        print(msg)
