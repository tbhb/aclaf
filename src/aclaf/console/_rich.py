from typing import TYPE_CHECKING, Any, TextIO, override

from ._base import DEFAULT_END, DEFAULT_SEP, BaseConsole

if TYPE_CHECKING:
    try:  # noqa: SIM105 - contextlib.suppress not available in TYPE_CHECKING
        from rich import (
            console as rich_console,
        )
    except ImportError:
        pass  # Rich is optional

try:
    from rich import console as rich_console
except ImportError as e:
    _rich_import_error = e
else:
    _rich_import_error = None

RICH_AVAILABLE = _rich_import_error is None


class RichConsole(BaseConsole):
    def __init__(
        self,
        file: TextIO | None = None,
        *,
        console: "rich_console.Console | None" = None,
    ) -> None:
        if not RICH_AVAILABLE:
            msg = "The 'rich' library is required for RichConsole."
            raise ImportError(msg) from _rich_import_error

        super().__init__(file=file)

        self._console: rich_console.Console = (
            console or rich_console.Console(file=file)  # pyright: ignore[reportPossiblyUnboundVariable]
        )

    @override
    def print(
        self,
        *objects: Any,  # pyright: ignore[reportExplicitAny, reportAny]
        sep: str = DEFAULT_SEP,
        end: str = DEFAULT_END,
        flush: bool = False,
    ) -> None:
        self._console.print(*objects, sep=sep, end=end)
