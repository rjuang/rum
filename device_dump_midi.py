# name=RUM Library Debugger Tool
""" Debugger utility to dump out midi event messages in FL Studio. """
from daw import flstudio

import playlist
import channels
import mixer
import patterns
import arrangement
import ui
import transport
import device
import plugins
import general
import launchMapPages

DUMP_API = False

def dump_api():
    # Programatically generate mocks
    modules = [
        playlist,
        channels,
        mixer,
        patterns,
        arrangement,
        ui,
        transport,
        device,
        plugins,
        general,
        launchMapPages
    ]

    print('========== [ BEGIN copy output below ] ==================')
    for m in modules:
        generate_stubs(m)
    print('========== [ END   copy output above ] ==================')


def generate_stubs(module):
    print(f'# {module.__name__}.py')
    for method_name in dir(module):
        if method_name.startswith('__'):
            continue
        method = getattr(module, method_name)
        if callable(method):
            print(f'def {method_name}(*args, **kwargs):')
            print(f'    """ {method.__doc__} """')
            print(f'    pass')
        else:
            print(f'{method_name} = {method}')


def OnInit():
    print('Loaded RUM Library Debugger Tool')
    if DUMP_API:
        dump_api()


def OnMidiMsg(event):
    msg = flstudio.Midi.to_midi_message(event)
    print(msg)
