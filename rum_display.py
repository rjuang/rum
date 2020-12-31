""" Classes for managing display state in a midi controller. """


class DirectDisplay:
    """ Basic simple display that maintains a set of chars to display.

    DirectDisplay simply holds the line contents that will be displayed on
    the LCD screen represented. These are represented as arrays of arrays of
    chars. The display also offers a push method to sync to a destination
    buffer.
    """
    class Builder:
        def __init__(self):
            # Display limit defaults
            self._num_lines = 2
            self._line_width = 16
            self._push_fn = None

        def set_lines(self, num_lines):
            self._num_lines = num_lines
            return self

        def set_line_width(self, num_chars):
            self._line_width = num_chars
            return self

        def push_with(self, push_fn):
            self._push_fn = push_fn
            return self

        def build(self):
            return DirectDisplay(self._num_lines,
                                 self._line_width,
                                 push_fn=self._push_fn)

    def __init__(self, num_lines, chars_per_line, push_fn=None):
        self._num_lines = num_lines
        self._num_chars = chars_per_line
        self._lines = [[' ' for _ in range(self._num_chars)]
                       for _ in range(num_lines)]
        self._push_fn = push_fn

    def height(self):
        return len(self)

    def width(self):
        return self._num_chars

    def __len__(self):
        return self._num_lines

    def __getitem__(self, key):
        return self._lines[key]

    def _fix_width(self, line):
        """ Fix the limit (either truncate or pad) to self._num_chars. """
        padding = ' ' * self._num_chars
        line += padding
        return line[:self._num_chars]

    def __setitem__(self, key, value):
        self._lines[key][:] = self._fix_width(value)

    def push(self):
        """ Push the buffer contents into the display. """
        if self._push_fn is None:
            return
        self._push_fn(self._lines)

    def __repr__(self):
        return '\n'.join([''.join(arr) for arr in self._lines])


class DisplayWindow:
    """ Creates a window view into a display. """
    def __init__(self, display_buffer: DirectDisplay, line_range=None,
                 char_range=None):
        self._display_buffer = display_buffer
        if line_range is None:
            line_range = (0, display_buffer.height())

        if char_range is None:
            char_range = (0, display_buffer.width())

        self._line_range = line_range
        self._char_range = char_range

    def __len__(self):
        return self._line_range[1] - self._line_range[0]

    def height(self):
        return len(self)

    def width(self):
        return self._char_range[1] - self._char_range[0]

    def _get_line(self, idx):
        base_idx = self._line_range[0] if idx >= 0 else self._line_range[1]
        return self._display_buffer[base_idx + idx]

    def __getitem__(self, key):
        return self._get_line(key)[self._char_range[0]:self._char_range[-1]]

    def _fix_width(self, line):
        """ Fix the limit (either truncate or pad) to self._num_chars. """
        num_chars = self._char_range[1] - self._char_range[0]
        padding = ' ' * num_chars
        line += padding
        return line[:num_chars]

    def __setitem__(self, key, value):
        self._get_line(key)[self._char_range[0]:self._char_range[-1]] = self._fix_width(value)

    def push(self):
        self._display_buffer.push()

    def __repr__(self):
        lines = [''.join(self._get_line(i)) for i in range(*self._line_range)]
        return '\n'.join(lines)