from threading import Lock
from typing import Callable

from irene.face.abc import MuteGroup, Muteable


class MuteGroupImpl(MuteGroup):
    def __init__(self) -> None:
        self._items: list[Muteable] = []
        self._mx = Lock()
        self._mute_count = 0

    def _is_muted(self) -> bool:
        return self._mute_count > 0

    def add_item(self, item: Muteable) -> Callable[[], None]:
        removed = False

        def _remove():
            nonlocal removed

            with self._mx:
                if removed:
                    raise AssertionError()

                self._items.remove(item)
                removed = True

                if self._is_muted():
                    item.unmute()

        with self._mx:
            self._items.append(item)

            if self._is_muted():
                item.mute()

        return _remove

    def mute(self):
        with self._mx:
            was_muted = self._is_muted()

            self._mute_count += 1

            if self._is_muted() and not was_muted:
                for item in self._items:
                    item.mute()

    def unmute(self):
        with self._mx:
            if self._mute_count <= 0:
                raise AssertionError()

            was_muted = self._is_muted()

            self._mute_count -= 1

            if not self._is_muted() and was_muted:
                for item in self._items:
                    item.unmute()


class _NullMuteGroup(MuteGroup):
    def add_item(self, item: Muteable) -> Callable[[], None]:
        return lambda: None

    def mute(self):
        pass

    def unmute(self):
        pass


NULL_MUTE_GROUP = _NullMuteGroup()
