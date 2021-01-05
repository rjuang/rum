from rum.scheduling import Scheduler


class Recorder:
    """ Generic event sequence recorder and player.

    This class implements a generic event recorder that can be played back with
    the same relative time offsets. This can be used for recording/playing back
    UI events, MIDI notes, button presses, keyboard typing, etc. The data
    type is generic and the playback function is provided via the constructor.
    As such, the recorder can be re-purposed
    """
    def __init__(self, scheduler: Scheduler, playback_fn=None):
        self._scheduler = scheduler

        # List of tuples containing (time, channel note, velocity)
        self._recording_pattern_id = None
        # Function to receive the recorded data event
        self._playback_fn = playback_fn
        self._pattern_map = {}
        # Maps a pattern id to the current play tasks
        self._play_task_map = {}
        # Maps a pattern id to the next scheduled loop task.
        self._loop_task_map = {}

    def on_data_event(self, timestamp_ms, data):
        """ Called when new data to potentially record is produced.

        Calls to this method when the recorder is not recording will be ignored.
        When recording, the data provided here will be saved to memory. This
        same data will then be provided to the playback function during
        playback.

        :param timestamp_ms:  timestamp (in milliseconds) of the data
        :param data: arbitrary type representing the data to record.
        """
        if self._recording_pattern_id is None:
            return
        key = self._recording_pattern_id
        self._pattern_map[key].append((timestamp_ms, data))

    def start_recording(self, pattern_id):
        """ Start recording incoming notes for the specified pattern id. """
        self._recording_pattern_id = pattern_id
        self._pattern_map[pattern_id] = []

    def stop_recording(self):
        """ Stop recording incoming notes. """
        self._recording_pattern_id = None

    def is_recording(self):
        """ Return true if currently recording a pattern. """
        return self._recording_pattern_id is not None

    def play(self, pattern_id, loop=False, loop_delay_ms=0):
        """ Schedule a pattern for playback when pressed.

        :param pattern_id: the pattern to playback.
        :param loop: set to True to keep looping the playback.
        :param loop_delay_ms: number of milliseconds to delay after pattern
        finishes before looping.
        :return True if pattern to play is found. False if no pattern to play.
        """
        if pattern_id not in self._pattern_map:
            return False
        pattern = self._pattern_map[pattern_id]
        if not pattern:
            # Nothing to play
            return False

        if loop and pattern_id in self._loop_task_map:
            # Already playing loop. Don't play the same pattern in loops
            # twice, but allow overlap if playing once.
            return True
        self._play_pattern(pattern_id, pattern, loop, loop_delay_ms)
        return True

    def _play_pattern(self, pattern_id, pattern, loop, loop_delay_ms):
        if pattern_id not in self._play_task_map:
            self._play_task_map[pattern_id] = set()
        base_ms = pattern[0][0]
        for timestamp_ms, data in pattern:
            delay_ms = timestamp_ms - base_ms
            self._play_data(pattern_id, delay_ms, data)
        if loop and delay_ms > 0:
            # Don't schedule something that will keep playing now
            self._schedule_loop(pattern_id,
                                delay_ms + loop_delay_ms,
                                loop_delay_ms,
                                pattern)

    def _play_data(self, pattern_id, delay_ms, data):
        if delay_ms <= 0:
            # Check if the data needs to be played now.
            self._playback_fn(data)
        else:
            task = self._scheduler.schedule(lambda: self._playback_fn(data),
                                            delay_ms=delay_ms)
            self._play_task_map[pattern_id].add(task)
            self._schedule_delete_task(pattern_id, task, delay_ms)

    def _schedule_delete_task(self, pattern_id, task, delay_ms):
        def _clean_task():
            if pattern_id not in self._play_task_map: return
            self._play_task_map[pattern_id].discard(task)
        self._scheduler.schedule(_clean_task, delay_ms=delay_ms)

    def _schedule_loop(self, pattern_id, delay_ms, loop_delay_ms, pattern):
        task = self._scheduler.schedule(
            lambda: self._play_pattern(pattern_id, pattern, True,
                                       loop_delay_ms),
            delay_ms=delay_ms)
        if pattern_id in self._loop_task_map:
            # Cancel any pre-existing loop (just in case) before overwriting.
            self._scheduler.cancel(self._loop_task_map[pattern_id])
        self._loop_task_map[pattern_id] = task

    def cancel_loop(self, pattern_id):
        """ Cancel looping for the pattern allowing it to finish playing.

        :param pattern_id:  the id of the pattern to cancel looping.
        """
        if pattern_id in self._loop_task_map:
            self._scheduler.cancel(self._loop_task_map[pattern_id])
            del self._loop_task_map[pattern_id]

    def stop(self, pattern_id):
        """ Stop playing any loop with pattern_id immediately. """
        self.cancel_loop(pattern_id)
        if pattern_id in self._play_task_map:
            for task in self._play_task_map[pattern_id]:
                self._scheduler.cancel(task)
            self._play_task_map[pattern_id] = set()

    def stop_all(self):
        """ Stop everything from playing immediately. """
        # Cancel all loops
        for loop_task in self._loop_task_map.values():
            self._scheduler.cancel(loop_task)
        self._loop_task_map.clear()

        # Cancel all pending tasks
        for task_set in self._play_task_map.values():
            for task in task_set:
                self._scheduler.cancel(task)
        self._play_task_map.clear()
