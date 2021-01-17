# name=RUM Library Debugger Tool
""" Debugger utility to dump out midi event messages in FL Studio. """
from daw import flstudio

import playlist
import channels
import midi
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
        midi,
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
    print('# {}.py'.format(module.__name__))
    for method_name in dir(module):
        if method_name.startswith('__'):
            continue
        method = getattr(module, method_name)
        if callable(method):
            print('def {}(*args, **kwargs):'.format(method_name))
            print('    """ {} """'.format(method.__doc__))
            print('    pass')
        else:
            print('{} = {}'.format(method_name, method))


def OnInit():
    print('Loaded RUM Library Debugger Tool')
    if DUMP_API:
        dump_api()


def OnMidiMsg(event):
    msg = flstudio.Midi.to_midi_message(event)
    print(msg)
