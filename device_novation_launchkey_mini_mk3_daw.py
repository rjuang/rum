# name=RUM Novation Launchkey Mini Mk3 DAW
# url=https://github.com/rjuang/rum
# receiveFrom=RUM Novation Launchkey Mini Mk3 MIDI
from daw import flstudio
from daw.flstudio import register
from device_profile.novation import LaunchkeyMk3
from rum.matchers import midi_has
from rum.midi import MidiMessage
from rum.decorators import trigger_when


@trigger_when(midi_has(status=LaunchkeyMk3.SOLID_LED_STATUS_CMD))
def set_led_color(m: MidiMessage):
    msg = LaunchkeyMk3.new_command().light_color(m.data1, m.data2).build()
    flstudio.Device.send_sysex_message(msg)


@trigger_when(midi_has(status=LaunchkeyMk3.BLINK_LED_STATUS_CMD))
def set_blinking_led(m: MidiMessage):
    msg = LaunchkeyMk3.new_command().blinking_light(m.data1, m.data2).build()
    flstudio.Device.send_sysex_message(msg)


@register
def OnInit():
    print('Loaded RUM Device Novation Launchkey Mini MK3 (DAW)')


@register
def OnIdle():
    pass


@register
def OnMidiMsg(event):
    msg = MidiMessage(event.status, event.data1, event.data2)
    print(msg)
