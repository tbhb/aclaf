import threading
from typing import TextIO, override

from aclaf.console._base import BaseConsole


class BasicConsole(BaseConsole):
    def __init__(self, file: TextIO | None = None) -> None:
        super().__init__(file=file)
        self._lock: threading.Lock = threading.Lock()

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
            _ = self._file.write(output)
            if flush:
                self._file.flush()
