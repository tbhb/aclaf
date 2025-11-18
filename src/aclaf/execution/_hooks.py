from typing import (
    TYPE_CHECKING,
    Protocol,
    runtime_checkable,
)

from ._hook_registry import Hook

if TYPE_CHECKING:
    from collections.abc import Mapping
    from contextlib import (
        AbstractContextManager,
    )
    from typing import TypeAlias

    from aclaf.parser import ParserConfiguration, ParseResult
    from aclaf.response import ResponseType
    from aclaf.types import ParameterValueMappingType

    from ._command import RuntimeCommand
    from ._context import Context

    ConversionResult: TypeAlias = tuple[
        ParameterValueMappingType | None, Mapping[str, Exception] | None
    ]


@runtime_checkable
class AroundParseHook(Hook, Protocol):
    def __call__(
        self,
        command: "RuntimeCommand",
        parse_config: "ParserConfiguration",
    ) -> "AbstractContextManager[ParseResult]": ...


@runtime_checkable
class BeforeParseHook(Hook, Protocol):
    def __call__(
        self, command: "RuntimeCommand", parse_config: "ParserConfiguration"
    ) -> "ParserConfiguration | None": ...


@runtime_checkable
class AfterParseHook(Hook, Protocol):
    def __call__(
        self, command: "RuntimeCommand", parse_result: "ParseResult"
    ) -> "ParseResult | None": ...


@runtime_checkable
class ParseErrorHook(Hook, Protocol):
    def __call__(self, command: "RuntimeCommand", error: Exception) -> None: ...


@runtime_checkable
class AroundConversionHook(Hook, Protocol):
    def __call__(
        self,
        command: "RuntimeCommand",
        parse_result: "ParseResult",
    ) -> "AbstractContextManager[ConversionResult]": ...


@runtime_checkable
class BeforeConversionHook(Hook, Protocol):
    def __call__(
        self, command: "RuntimeCommand", parse_result: "ParseResult"
    ) -> None: ...


@runtime_checkable
class AfterConversionHook(Hook, Protocol):
    def __call__(
        self,
        command: "RuntimeCommand",
        parse_result: "ParseResult",
        converted: "ParameterValueMappingType | None" = None,
        errors: "Mapping[str, Exception] | None" = None,
    ) -> tuple[
        "ParameterValueMappingType | None", "Mapping[str, Exception] | None"
    ]: ...


@runtime_checkable
class ConversionErrorHook(Hook, Protocol):
    def __call__(
        self,
        command: "RuntimeCommand",
        parse_result: "ParseResult",
        error: Exception,
    ) -> None: ...


@runtime_checkable
class BeforeValidationHook(Hook, Protocol):
    def __call__(
        self,
        command: "RuntimeCommand",
        parse_result: "ParseResult",
        converted: "ParameterValueMappingType | None",
        errors: "Mapping[str, Exception] | None",
    ) -> tuple[
        "ParameterValueMappingType | None", "Mapping[str, Exception] | None"
    ]: ...


@runtime_checkable
class AfterValidationHook(Hook, Protocol):
    def __call__(
        self,
        command: "RuntimeCommand",
        parse_result: "ParseResult",
        validated: "ParameterValueMappingType | None",
        errors: "Mapping[str, Exception] | None",
    ) -> tuple[
        "ParameterValueMappingType | None", "Mapping[str, Exception] | None"
    ]: ...


@runtime_checkable
class ValidationErrorHook(Hook, Protocol):
    def __call__(
        self,
        command: "RuntimeCommand",
        parse_result: "ParseResult",
        error: Exception,
    ) -> None: ...


@runtime_checkable
class BeforeContextSetupHook(Hook, Protocol):
    def __call__(
        self,
        command: "RuntimeCommand",
        parse_result: "ParseResult",
        validated: "ParameterValueMappingType | None",
        errors: "Mapping[str, Exception] | None",
    ) -> tuple[
        "ParameterValueMappingType | None", "Mapping[str, Exception] | None"
    ]: ...


@runtime_checkable
class AfterContextSetupHook(Hook, Protocol):
    def __call__(
        self, command: "RuntimeCommand", context: "Context"
    ) -> "Context | None": ...


@runtime_checkable
class BeforeExecutionHook(Hook, Protocol):
    def __call__(self, command: "RuntimeCommand", context: "Context") -> bool: ...


@runtime_checkable
class BeforeExecutionHookAsyncFunction(Hook, Protocol):
    async def __call__(self, command: "RuntimeCommand", context: "Context") -> bool: ...


class CancelExecution(Exception):  # noqa: N818
    """Exception to indicate that execution should be cancelled."""


@runtime_checkable
class AfterExecutionHook(Hook, Protocol):
    def __call__(
        self,
        command: "RuntimeCommand",
        context: "Context",
        response: "ResponseType | None",
    ) -> None: ...


@runtime_checkable
class AfterExecutionHookAsyncFunction(Hook, Protocol):
    async def __call__(
        self,
        command: "RuntimeCommand",
        context: "Context",
        response: "ResponseType | None",
    ) -> None: ...


@runtime_checkable
class ExecutionErrorHook(Hook, Protocol):
    def __call__(
        self, command: "RuntimeCommand", context: "Context", error: Exception
    ) -> None: ...


@runtime_checkable
class ExecutionErrorHookAsyncFunction(Hook, Protocol):
    async def __call__(
        self, command: "RuntimeCommand", context: "Context", error: Exception
    ) -> None: ...


@runtime_checkable
class BeforeResponseHook(Hook, Protocol):
    def __call__(
        self,
        command: "RuntimeCommand",
        context: "Context",
        response: "ResponseType | None",
    ) -> "ResponseType | None": ...


@runtime_checkable
class BeforeResponseHookAsyncFunction(Hook, Protocol):
    async def __call__(
        self,
        command: "RuntimeCommand",
        context: "Context",
        response: "ResponseType | None",
    ) -> "ResponseType | None": ...


@runtime_checkable
class AfterResponseHook(Hook, Protocol):
    def __call__(
        self,
        command: "RuntimeCommand",
        context: "Context",
        response: "ResponseType | None",
    ) -> None: ...


@runtime_checkable
class AfterResponseHookAsyncFunction(Hook, Protocol):
    async def __call__(
        self,
        command: "RuntimeCommand",
        context: "Context",
        response: "ResponseType | None",
    ) -> None: ...


@runtime_checkable
class ResponseErrorHook(Hook, Protocol):
    def __call__(
        self,
        command: "RuntimeCommand",
        context: "Context",
        response: "ResponseType | None",
        error: Exception,
    ) -> None: ...


RuntimeHookType = (
    BeforeParseHook
    | AfterParseHook
    | ParseErrorHook
    | BeforeConversionHook
    | AfterConversionHook
    | ConversionErrorHook
    | BeforeValidationHook
    | AfterValidationHook
    | ValidationErrorHook
    | BeforeContextSetupHook
    | AfterContextSetupHook
    | BeforeExecutionHook
    | BeforeExecutionHookAsyncFunction
    | AfterExecutionHook
    | AfterExecutionHookAsyncFunction
    | ExecutionErrorHook
    | ExecutionErrorHookAsyncFunction
    | BeforeResponseHook
    | BeforeResponseHookAsyncFunction
    | AfterResponseHook
    | AfterResponseHookAsyncFunction
    | ResponseErrorHook
)
