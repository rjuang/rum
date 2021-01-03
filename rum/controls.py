""" Contains classes that combine multiple classes to create complex controls.

The purpose of this class is to simplify the construction of common control
components (e.g. blinkable lights) by combining various classes into a single
class.
"""
from rum.animations import BlinkingAnimation, SequentialAnimation
from rum.lights import ToggleLight
from rum.scheduling import Scheduler


class Blinkable:
    """ Interface for classes with lights that can be made blinking. """
    def start_blinking(self): raise NotImplementedError()
    def stop_blinking(self): raise NotImplementedError()
    def set_blink_interval(self, interval_ms): raise NotImplementedError()
    def is_blinking(self): raise NotImplementedError()


class Beatable:
    """ Interface for classes that can sync to a beat. """
    def beat(self): raise NotImplementedError()
    def reset(self): raise NotImplementedError()


class BlinkableLight(Blinkable, ToggleLight):
    """ A light that can be put into a blinking state. """

    def __init__(self, light: ToggleLight, scheduler: Scheduler,
                 blink_interval_ms=1000):
        self._light = light
        self._blink_animation = BlinkingAnimation(
            light, scheduler, blink_interval_ms)

    def __bool__(self):
        return bool(self._light)

    def toggle(self, bool_value=None):
        if self._blink_animation.is_animation_running():
            self._blink_animation.stop_animation()
        return self._light.toggle(bool_value=bool_value)

    def get(self):
        return self._light.get()

    def set(self, value, force_update=False):
        if self._blink_animation.is_animation_running():
            self._blink_animation.stop_animation()
        self._light.set(value, force_update=force_update)

    def start_blinking(self):
        self._blink_animation.start_animation()

    def stop_blinking(self):
        self._blink_animation.stop_animation()

    def set_blink_interval(self, interval_ms):
        self._blink_animation.set_update_interval(interval_ms)

    def is_blinking(self):
        return self._blink_animation.is_animation_running()


class Metronome(Beatable):
    """ Makes a list of lights into a metronome.

    A metronome toggles each light in the provided sequence one at a time. When
    the last light is reached, it starts over.
    """

    def __init__(self, scheduler: Scheduler, lights: 'list[ToggleLight]'):
        pattern = [[l] for l in lights]
        if len(pattern) == 1:
            # In the event the pattern only has 1 frame (i.e. 1 element in
            # lights), add a frame where all lights are off.
            pattern.append([])
        self._animation = SequentialAnimation(pattern, scheduler)

    def beat(self):
        """ Step a beat in the metronome. """
        self._animation.step_animation()

    def reset(self):
        """ Resets the metronome so that it starts from the first beat. """
        self._animation.reset_animation()
