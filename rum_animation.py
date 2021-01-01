from rum_lights import ToggleLight
from rum_threading import Scheduler


class Animation:
    """ Interface for an animation concept. """
    def start(self): raise NotImplementedError()
    def stop(self): raise NotImplementedError()
    def is_running(self): raise NotImplementedError()
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

    def start(self):
        """ Starts running the blink animation.

        This command is a no-op if the animation is already started.
        """
        if self._run_animation:
            # Animation already scheduled.
            return
        self._run_animation = True
        self._animation_task = self._scheduler.schedule(
            self._toggle_blink, delay_ms=self._update_interval_ms)

    def stop(self):
        """ Cancels the any currently running animation.

        This command is a no-op if the animation is already stopped.
        """
        if not self._run_animation:
            return
        self._run_animation = False
        if self._animation_task is not None:
            self._scheduler.cancel(self._animation_task)
        self._animation_task = None

    def is_running(self):
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

    def _animate_frame(self):
        if not self._run_animation:
            return

        current_frame = set(self._light_frames[self._current_index])
        turn_off = self._last_frame.difference(current_frame)

        for light in turn_off:
            light.toggle(bool_value=False)

        for light in current_frame:
            light.toggle(bool_value=True)

        self._last_frame = current_frame
        self._current_index += 1
        self._current_index %= len(self._light_frames)
        self._animation_task = self._scheduler.schedule(
            self._animate_frame, delay_ms=self._update_interval_ms)

    def start(self):
        if self._run_animation:
            return
        self._run_animation = True
        self._animation_task = self._scheduler.schedule(
            self._animate_frame, delay_ms=self._update_interval_ms)

    def stop(self):
        if not self._run_animation:
            return

        self._run_animation = False
        if self._animation_task is not None:
            self._scheduler.cancel(self._animation_task)
            self._animation_task = None

    def is_running(self):
        return self._run_animation

    def set_update_interval(self, interval_ms):
        self._update_interval_ms = interval_ms

