# name=RUM Novation Launchkey Mini Mk3 DAW
# url=https://github.com/rjuang/rum
# receiveFrom=RUM Novation Launchkey Mini Mk3 MIDI
from daw import flstudio
from device_profile.novation import LaunchkeyMk3
from rum import matchers
from rum.matchers import when
from rum.midi import MidiMessage, MidiProcessor

def set_led_color(m: MidiMessage):
    msg = LaunchkeyMk3.new_command().light_color(m.data1, m.data2).build()
    print(f'Set led color: {m}')
    flstudio.Device.send_sysex_message(msg)

def set_blinking_led(m: MidiMessage):
    msg = LaunchkeyMk3.new_command().blinking_light(m.data1, m.data2).build()
    print(f'Set blinking color: {m}')
    flstudio.Device.send_sysex_message(msg)

_processor = MidiProcessor().add(
    when(matchers.status_eq(LaunchkeyMk3.SOLID_LED_STATUS_CMD)).then(
        set_led_color),
    when(matchers.status_eq(LaunchkeyMk3.BLINK_LED_STATUS_CMD)).then(
        set_blinking_led)
)

def OnInit():
    print('Loaded RUM Device Novation Launchkey Mini MK3 (DAW)')


def OnMidiMsg(event):
    msg = MidiMessage(event.status, event.data1, event.data2)
    print(msg)
    _processor.process(msg)

