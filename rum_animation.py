from rum_lights import ToggleLight
from rum_threading import Scheduler


class Animation:
    """ Interface for an animation concept. """
    def start_animation(self, initial_delay=True): raise NotImplementedError()
    def step_animation(self): raise NotImplementedError()
    def stop_animation(self): raise NotImplementedError()
    def reset_animation(self): raise NotImplementedError()
    def is_animation_running(self): raise NotImplementedError()
    def set_update_interval(self, interval_ms): raise NotImplementedError()


class BlinkingAnimation(Animation):
    """ Controls blinking a light source.

    If a ColorLight source needs to be blinked, then it needs to be re-defined
    (via a facade/view pattern) as a Light source.
    """

    def __init__(self, light: ToggleLight, scheduler: Scheduler,
                 update_interval_ms=1000):
        self._light = light
        self._scheduler = scheduler
        self._update_interval_ms = update_interval_ms
        self._animation_task = None
        self._run_animation = False

    def _toggle_blink(self):
        # Check if animation got stopped.
        if not self._run_animation:
            return
        self._light.toggle()
        self._animation_task = self._scheduler.schedule(
            self._toggle_blink, delay_ms=self._update_interval_ms)

    def start_animation(self, initial_delay=True):
        """ Starts running the blink animation.

        This command is a no-op if the animation is already started.
        """
        if self._run_animation:
            # Animation already scheduled.
            return
        self._run_animation = True
        self._animation_task = self._scheduler.schedule(
            self._toggle_blink, delay_ms=self._update_interval_ms)

    def step_animation(self):
        """ Manually step blink the animation. """
        self._light.toggle()

    def stop_animation(self):
        """ Cancels the any currently running animation.

        This command is a no-op if the animation is already stopped.
        """
        if not self._run_animation:
            return
        self._run_animation = False
        if self._animation_task is not None:
            self._scheduler.cancel(self._animation_task)
        self._animation_task = None

    def reset_animation(self):
        # No-op since blinking just starts off from where last left off.
        pass

    def is_animation_running(self):
        """ Returns True if the blink animation is scheduled/running."""
        return self._run_animation

    def set_update_interval(self, interval_ms):
        """ Update how fast the light blinks. """
        self._update_interval_ms = interval_ms


class SequentialAnimation(Animation):
    """ Controls lighting patterns of lights sequentially in time.

    SequentialAnimation generalizes animation by representing light animation
    as a sequence of light patterns to display per time step. The patterns are
    specified as a list of pattern frames. A pattern frame is a list of
    ToggleLights that should be the only lights that are on for that frame.
    """

    def __init__(self, light_frames: list[list[ToggleLight]],
                 scheduler: Scheduler,
                 update_interval_ms=1000,
                 loop=True):
        self._light_frames = light_frames
        self._scheduler = scheduler
        self._current_index = 0
        self._update_interval_ms = update_interval_ms
        self._loop = loop
        self._run_animation = False
        self._animation_task = None
        self._last_frame = set()

        # Get a list of all lights involved so we can quickly reset them
        self._all_lights = set()
        for lights in light_frames:
            self._all_lights = self._all_lights.union(lights)

    def _animate_step(self):
        current_frame = set(self._light_frames[self._current_index])
        if self._current_index == 0:   # For first frame, reset all lights.
            turn_off = self._all_lights.difference(current_frame)
        else:
            turn_off = self._last_frame.difference(current_frame)

        for light in turn_off:
            light.toggle(bool_value=False)

        for light in current_frame:
            light.toggle(bool_value=True)

        self._last_frame = current_frame
        self._current_index += 1
        self._current_index %= len(self._light_frames)

    def _schedule_animation(self):
        if not self._run_animation:
            return
        self._animate_step()
        if not self._loop and self._current_index == 0:
            # If not looping, stop animation when loop back.
            self.stop_animation()
        self._animation_task = self._scheduler.schedule(
            self._schedule_animation, delay_ms=self._update_interval_ms)

    def start_animation(self, initial_delay=False):
        if self._run_animation:
            return
        self._run_animation = True
        delay_ms = self._update_interval_ms if initial_delay else 0
        self._animation_task = self._scheduler.schedule(
            self._schedule_animation, delay_ms=delay_ms)

    def step_animation(self):
        self._animate_step()

    def stop_animation(self):
        if not self._run_animation:
            return

        self._run_animation = False
        if self._animation_task is not None:
            self._scheduler.cancel(self._animation_task)
            self._animation_task = None

    def reset_animation(self):
        # Reset the animation to start from beginning.
        self._current_index = 0

    def is_animation_running(self):
        return self._run_animation

    def set_update_interval(self, interval_ms):
        self._update_interval_ms = interval_ms
