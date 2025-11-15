from ._base import DEFAULT_END, DEFAULT_SEP, BaseConsole
from ._protocol import SupportsConsole
from ._rich import RICH_AVAILABLE, RichConsole

if RICH_AVAILABLE:
    DefaultConsole = RichConsole
else:
    from ._basic import BasicConsole

    DefaultConsole = BasicConsole

__all__ = [
    "DEFAULT_END",
    "DEFAULT_SEP",
    "RICH_AVAILABLE",
    "BaseConsole",
    "BasicConsole",
    "DefaultConsole",
    "RichConsole",
    "SupportsConsole",
]
