""" Central location to hold all state information. """


class DefaultDict:
    """ Alternate implementation of defaultdict.

     This is needed as some DAW's python environment does not include the
     standard collections python library.
     """

    def __init__(self, default_fn=None):
        self._new_entry = default_fn
        self._dict = {}

    def __getitem__(self, key):
        if key not in self._dict:
            self._dict[key] = self._new_entry()
        return self._dict[key]

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __delitem__(self, key):
        if key in self._dict:
            del self._dict[key]

    def __iter__(self):
        return self._dict.__iter__()

    def __len__(self):
        return len(self._dict)

    def __contains__(self, key):
        return self._dict.__contains__(key)

    def clear(self):
        return self._dict.clear()

    def keys(self):
        return self._dict.keys()


""" Contains a mapping of button names to whether they are currently held. """
button_down = DefaultDict(bool)

""" Contains a mapping of all encoders to the accumulated differential value of 
the encoder. """
encoders = DefaultDict(float)

""" Contains a mapping of all sliders to the current value of the slider. """
sliders = DefaultDict(float)
