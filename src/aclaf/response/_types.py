from collections.abc import AsyncGenerator, Generator

from aclaf.console import SupportsConsole
from aclaf.protocols import Printable

SupportsResponseType = Printable | SupportsConsole


SyncResponseType = (
    SupportsResponseType
    | Generator[SupportsResponseType, None, SupportsResponseType | None]
)

AsyncResponseType = SupportsResponseType | AsyncGenerator[SupportsResponseType, None]

ResponseType = SyncResponseType | AsyncResponseType
