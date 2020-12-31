""" Classes for managing display state in a midi controller. """
from rum_threading import Scheduler


class Display:
    """ Pseudo-interface that all displays must implement.

     A display can show a field of characters where the rows are lines of
     text and the columns are individual characters of each line. It is assumed
     that displays are rectangular fields.
     """
    def width(self):
        """ Returns the width (num of chars per line) of the display. """
        raise NotImplementedError()

    def height(self):
        """ Returns the height (number of lines) of the display. """
        raise NotImplementedError()

    def push(self):
        """ Push the contents in this instance to the actual hardware. """
        raise NotImplementedError()


class DirectDisplay(Display):
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
            """ Specify number of lines the display supports (default: 2). """
            self._num_lines = num_lines
            return self

        def set_line_width(self, num_chars):
            """ Specify number of chars per display line (default: 16). """
            self._line_width = num_chars
            return self

        def push_with(self, push_fn):
            """ Specify function for pushing display text to the actual display.

            :param push_fn: function that takes a list of lines to display. Each
            line is a list of characters with exactly the specified number of
            chars that fit the display. The function is resposible for pushing
            the character lines to the display. If None is specified (default),
            push calls are dropped. """
            self._push_fn = push_fn
            return self

        def build(self):
            """ Constructs a DirectDisplay with the specified parameters. """
            return DirectDisplay(self._num_lines,
                                 self._line_width,
                                 push_fn=self._push_fn)

    def __init__(self, num_lines, chars_per_line, push_fn=None):
        self._num_lines = num_lines
        self._num_chars = chars_per_line
        self._lines = [[' ' for _ in range(self._num_chars)]
                       for _ in range(num_lines)]
        self._push_fn = push_fn

    def __len__(self):
        return self._num_lines

    def __getitem__(self, key):
        return self._lines[key]

    def __setitem__(self, key, value):
        self._lines[key][:] = self._fix_width(value)

    def __repr__(self):
        return '\n'.join([''.join(arr) for arr in self._lines])

    def _fix_width(self, line):
        """ Fix the limit (either truncate or pad) to self._num_chars. """
        padding = ' ' * self._num_chars
        line += padding
        return line[:self._num_chars]

    def height(self):
        """ Returns the number of lines in the display. """
        return len(self)

    def width(self):
        """ Returns the number of characters per line in the display. """
        return self._num_chars

    def push(self):
        """ Push the buffer contents into the display. """
        if self._push_fn is None:
            return
        self._push_fn(self._lines)


class DisplayWindow(Display):
    """ Window of a Display that is a small sub-section of the display.

    The purpose of a window is to isolate a section of the display from the
    rest of the underlying display. This abstraction makes it easier to perform
    text animation (e.g. scrolling) for a portion of the display.
    """
    class Builder:
        def __init__(self, display: Display):
            self._display = display
            self._line_range = None
            self._char_range = None

        def line_range(self, start_line, end_line):
            """ Specify the lines to include in the display.

            If unspecified, the builder defaults to all lines.

            :param start_line: the starting line index to include
            :param end_line: the ending line index (not included) in the display
            :return: the builder instance for chaining additional setter calls.
            """
            self._line_range = (start_line, end_line)
            return self

        def char_range(self, start_col, end_col):
            """ Specify starting and ending column for all lines in the display.

            :param start_col: the starting column index to include.
            :param end_col: the ending column index (not included) in the
            display.
            :return: the builder instance for chaining additional setter calls.
            """
            self._char_range = (start_col, end_col)
            return self

        def build(self):
            """ Builds a DisplayWindow with the provided parameters. """
            return DisplayWindow(self._display,
                                 line_range=self._line_range,
                                 char_range=self._char_range)

    def __init__(self,
                 display: Display,
                 line_range=None,
                 char_range=None):
        self._display = display
        if line_range is None:
            line_range = (0, display.height())

        if char_range is None:
            char_range = (0, display.width())

        self._line_range = line_range
        self._char_range = char_range

    def __len__(self):
        return self._line_range[1] - self._line_range[0]

    def __getitem__(self, key):
        return self._get_line(key)[self._char_range[0]:self._char_range[-1]]

    def __setitem__(self, key, value):
        self._get_line(key)[self._char_range[0]:self._char_range[-1]] = self._fix_width(value)

    def __repr__(self):
        lines = [''.join(self._get_line(i)) for i in range(*self._line_range)]
        return '\n'.join(lines)

    def _get_line(self, idx):
        base_idx = self._line_range[0] if idx >= 0 else self._line_range[1]
        return self._display[base_idx + idx]

    def _fix_width(self, line):
        """ Fix the limit (either truncate or pad) to self._num_chars. """
        num_chars = self._char_range[1] - self._char_range[0]
        padding = ' ' * num_chars
        line += padding
        return line[:num_chars]

    def height(self):
        """ Returns the number of lines the window represents. """
        return len(self)

    def width(self):
        """ Returns the number of chars per line that the window represents. """
        return self._char_range[1] - self._char_range[0]

    def push(self):
        """ Trigger a push to render the text in the underlying display. """
        self._display.push()


class ScrollingDisplay(Display):
    """ Makes each line of the display a scrolling marquee.

    This class is an adaptor that modifies the behavior of an existing display
    so that the lines of text become scrolling in the event the line is longer
    than the display width.
    """
    def __init__(self,
                 display: Display,
                 scheduler: Scheduler,
                 scroll_interval_ms=250,
                 scroll_amount=1,
                 padding=2):
        self._display = display
        self._scheduler = scheduler
        self._scroll_interval_ms = scroll_interval_ms
        self._scroll_amount = scroll_amount
        self._padding = padding
        self._lines = ['' for _ in range(self._display.height())]
        self._offset_map = {i: 0 for i in range(self._display.height())}
        self._scrolling = set()

    def __len__(self):
        return len(self._display)

    def __getitem__(self, idx):
        return self._lines[idx]

    def __setitem__(self, idx, value):
        # Reset the scroll if user requests to set the value.
        self._offset_map[idx] = 0
        self._lines[idx] = value
        if idx not in self._scrolling:
            # Don't start another scrolling thread if line is already scrolling.
            self._update_display(idx)

    def _update_display(self, idx):
        if len(self._lines[idx]) <= self._display.width():
            # Text fits on display. No need to scroll.
            self._scrolling.discard(idx)
            self._display[idx] = self._lines[idx]
            return

        padded_line = f'{self._lines[idx]}{" " * self._padding}'
        offset = self._offset_map[idx]
        wrap_len = offset + self._display.width() - len(padded_line)
        wrap_str = padded_line[:wrap_len] if wrap_len > 0 else ''
        self._display[idx] = f'{padded_line[offset:]}{wrap_str}'
        self._offset_map[idx] += self._scroll_amount
        self._offset_map[idx] %= len(padded_line)
        self._scrolling.add(idx)
        self._scheduler.schedule(lambda: self._update_display(idx),
                                 delay_ms=self._scroll_interval_ms)

    def width(self):
        return self._display.width()

    def height(self):
        return self._display.height()

    def push(self):
        return self._display.push()
