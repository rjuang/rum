import _functools
import rum.lights
from daw import flstudio

from panels.abstract import Panel
from rum.midi import MidiMessage


_panels = {}


def get_panel(name):
    if name not in _panels:
        return None
    return _panels[name]


def new_color_toggle_light(led_id, light_fn, initial=0,
                           off_color=0, on_color=0x7F):
    update_fn = _functools.partial(light_fn, led_id)
    return rum.lights.ColorToggleLight(
        rum.lights.ColorLight(update_fn=update_fn, initial=initial),
        off_color=off_color, on_color=on_color)


def get_light(led_id):
    for panel in _panels.values():
        if led_id in panel:
            return panel[panel.index(led_id)]
    return None


class LightPanel(Panel):
    def __init__(self, name, led_ids, light_fn=None,
                 refresh_fn=None, initial=0, off_color=0, on_color=0x7F):
        super().__init__()
        self._name = name
        self._lights = None

        if light_fn is not None:
            self._lights = [
                new_color_toggle_light(led_id, light_fn, initial=initial,
                                       off_color=off_color, on_color=on_color)
                for led_id in led_ids]

        # In the event the decorator is used, then the decorated function will
        # be used as the lighting function.
        self._initial = initial
        self._off_color = off_color
        self._on_color = on_color
        self._led_ids = led_ids
        self._led_ids_to_index = {
            led_id: idx for idx, led_id in enumerate(led_ids)
        }
        self._light_fn = light_fn
        self._refresh_fn = refresh_fn
        _panels[name] = self

    def _refresh(self, flags):
        if flags & flstudio.REFRESH_CONTROLLER_LEDS == 0:
            return

        # Trigger refresh listener if one specified.
        if self._refresh_fn is not None:
            self._refresh_fn

        # Force all lights to refresh
        for light in self._lights:
            light.refresh()

    def _process_message(self, msg: MidiMessage):
        pass

    def _decorate(self, fn):
        self._light_fn = fn
        self._lights = [
            new_color_toggle_light(led_id, self._light_fn,
                                   initial=self._initial,
                                   off_color=self._off_color,
                                   on_color=self._on_color)
            for led_id in self._led_ids]

    def __getitem__(self, index):
        light: rum.ColorToggleLight = self._lights[index]
        return light

    def __setitem__(self, index, color):
        self._lights[index].set(color)

    def __len__(self):
        return len(self._lights)

    def __contains__(self, led_id):
        return led_id in self._led_ids_to_index

    def index(self, led_id):
        if led_id in self._led_ids_to_index:
            return self._led_ids_to_index[led_id]
        return -1

    def set_all_off_color(self, color):
        for light in self._lights:
            light.set_off_color(color)

    def set_all_on_color(self, color):
        for light in self._lights:
            light.set_on_color(color)

    def toggle_all(self, bool_value=None):
        for light in self._lights:
            light.toggle(bool_value=bool_value)

    def set_all(self, color):
        for light in self._lights:
            light.set(color)

