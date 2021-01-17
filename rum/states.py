""" Classes for maintaining state information between device and DAW.

The concept of a state here is to allow users to save and sync
stateful information between the device and DAW. Examples of stateful
information:
  - DAW recording status. If DAW is recording, then record light should be on,
    and subsequent button presses would trigger stop recording.
  - Button functionality. Is the button controlling mixer or channel currently.
"""


class State:
    """ Interface for a state.

    Any class that wants to act as a state must extend this class and override
    its methods.
    """
    def name(self):
        """ Returns string representing the name of the state. """
        raise NotImplementedError()

    def get(self):
        """ Returns the current value of the state. """
        raise NotImplementedError()

    def push(self):
        """ Push the current state value to its destination target. """
        raise NotImplementedError()

    def pull(self):
        """ Fetch the current state value from its source.

        :return: True if the state changed. False if state remained the same.
        """
        raise NotImplementedError()


class IterableState(State):
    """ State with a limited number of values that can be iterated through.

    A state variable with a limited number of values that it can be set to.

    States can:
      - sync their value with a source to read from via a "pull" operation
      - sync their value to a destination to write to via a "push" operation
      - directionally change the state value via next/prev calls.
    """

    class Builder:
        def __init__(self, name):
            self._name = name
            self._states = []
            self._initial_state = None
            self._pull_fn = None
            self._push_fn = None

        def add_state(self, state):
            self._states.append(state)
            return self

        def add_states(self, states):
            self._states.extend(states)
            return self

        def pull_with(self, pull_fn):
            self._pull_fn = pull_fn
            return self

        def push_with(self, push_fn):
            self._push_fn = push_fn
            return self

        def default_to(self, state):
            self._initial_state = state
            return self

        def build(self):
            return IterableState(
                self._name,
                self._states,
                initial=self._initial_state,
                pull_fn=self._pull_fn,
                push_fn=self._push_fn)

    def __init__(self, name: str, states, initial=None, pull_fn=None,
                 push_fn=None):
        if initial is None:
            initial = states[0]

        self._name = name
        self._states = tuple(states)
        self._index_map = {st: idx for idx, st in enumerate(states)}
        self._current_idx =  self._index_map[initial]
        self._pull_fn = pull_fn
        self._push_fn = push_fn

    def name(self):
        """ Returns the name of the state. """
        return self._name

    def get(self):
        """ Returns the current state. """
        return self._states[self._current_idx]

    def toggle_next(self):
        """ Toggle state to point to next value and return updated state. """
        self._current_idx = (self._current_idx + 1) % len(self._states)
        return self.get()

    def toggle_prev(self):
        """ Toggle state to point to previous and return updated state. """
        self._current_idx = (self._current_idx - 1) % len(self._states)
        return self.get()

    def push(self):
        """ Push the current state value to its destination target. """
        if self._push_fn is None:
            return
        self._push_fn(self.get())

    def pull(self):
        """ Fetch the current state value from its source.

        :return: True if the state changed. False if state remained the same.
        """
        if self._pull_fn is None:
            return
        state = self._pull_fn()
        updated_idx = self._index_map[state]
        different = updated_idx != self._current_idx
        self._current_idx = updated_idx
        return different

    def __repr__(self):
        return '{}={}'.format(self.name(), self.get())

