import inspect
from collections.abc import AsyncGenerator, Coroutine, Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, TypeAlias, cast, runtime_checkable
from typing_extensions import override

from .console import Console, SupportsConsole

if TYPE_CHECKING:
    from ._context import Context


@runtime_checkable
class SupportsPrint(Protocol):
    @override
    def __str__(self) -> str: ...


@runtime_checkable
class SupportsResponder(Protocol):
    def __response__(
        self, responder: "ConsoleResponder", context: "Context"
    ) -> None: ...


SupportsResponseType: TypeAlias = SupportsPrint | SupportsConsole | SupportsResponder


SyncResponseType: TypeAlias = (
    SupportsResponseType
    | Generator[SupportsResponseType, None, SupportsResponseType | None]
)

AsyncResponseType: TypeAlias = (
    SupportsResponseType | AsyncGenerator[SupportsResponseType, None]
)

ResponseType: TypeAlias = SyncResponseType | AsyncResponseType


class ResponderProtocol(Protocol):
    def respond(
        self, result: "SyncResponseType | None", context: "Context"
    ) -> None: ...

    async def respond_async(
        self, result: "AsyncResponseType | None", context: "Context"
    ) -> None: ...


@dataclass(slots=True, frozen=True)
class ConsoleResponder:
    console: "Console"

    def respond(self, result: "SyncResponseType | None", context: "Context") -> None:
        if result is None:
            return

        if inspect.isgenerator(result):
            try:
                while True:
                    value = cast("SupportsResponseType | None", next(result))
                    if value is not None:
                        self._print_value(value, context)
            except StopIteration as stop:
                stop_value = cast("SupportsResponseType | None", stop.value)
                if stop_value is not None:
                    self._print_value(stop_value, context)
        elif result is not None:
            self._print_value(result, context)

    async def respond_async(
        self, result: "AsyncResponseType | None", context: "Context"
    ) -> None:
        if result is None:
            return

        if inspect.isasyncgen(result):
            async_gen = cast("AsyncGenerator[SupportsResponseType, None]", result)
            async for value in async_gen:
                if value is not None:
                    self._print_value(value, context)
        elif inspect.iscoroutine(result):
            coroutine = cast(
                "Coroutine[object, object, SupportsResponseType | None]", result
            )
            awaited_result = await coroutine
            if awaited_result is not None:
                self._print_value(awaited_result, context)
        elif result is not None:
            self._print_value(result, context)

    def _print_value(
        self,
        value: SupportsResponseType | None,
        context: "Context",
    ) -> None:
        if value is None:
            return

        if isinstance(value, SupportsConsole):
            value.__console__(self.console)
        elif isinstance(value, SupportsResponder):
            value.__response__(self, context)
        else:
            self.console.print(value)
