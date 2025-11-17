import threading
from typing import TextIO, override

from aclaf.console._base import BaseConsole


class MockConsole(BaseConsole):
    def __init__(self, file: TextIO | None = None) -> None:
        super().__init__(file=file)
        self._lock: threading.Lock = threading.Lock()
        self.lines: list[str] = []

    @override
    def print(
        self,
        *objects: object,
        sep: str = " ",
        end: str = "\n",
        flush: bool = False,
    ) -> None:
        output = sep.join(str(obj) for obj in objects) + end
        with self._lock:
            self.lines.append(output)

    def get_output(self) -> str:
        with self._lock:
            return "".join(self.lines)

    def clear(self) -> None:
        with self._lock:
            self.lines.clear()
