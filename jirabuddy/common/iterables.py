from typing import Callable, Iterable, Any, Iterator


class IterUntil(Iterable):
    def __init__(self, action: Callable[[int], Iterable], until: Callable[[int, Any], bool]):
        self.action = action
        self.until = until
        self.loop = 0

    def __iter__(self) -> Iterator:
        while True:
            for item in self.action(self.loop):
                if self.until(self.loop, item):
                    return
                yield item
            self.loop += 1

