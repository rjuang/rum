# name=RUM Library Debugger Tool
""" Debugger utility to dump out midi event messages in FL Studio. """
from rum_midi import MidiMessage

def OnInit():
    print('Loaded RUM Library Debugger Tool')

def OnMidiMsg(event):
    msg = MidiMessage(event.status, event.data1, event.data2)
    print(msg)
