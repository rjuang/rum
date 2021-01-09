
# Flag for a full refresh (all bits are toggled on).
FULL_REFRESH = 0xFFFF_FFFF


class RefreshManager:
    """ Maintains list of refresh tasks when refresh is called.

    When

     """

    def __init__(self):
        self._listeners = []

    def refresh(self, flags):
        for fn in self._listeners:
            fn(flags)

    def add(self, listener):
        self._listeners.append(listener)

    def clear(self):
        self._listeners.clear()
        return self


_refresher = RefreshManager()


def get_refresh_manager():
    return _refresher
