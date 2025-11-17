from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    TypeAlias,
    TypedDict,
    cast,
)

from aclaf.console import DefaultConsole
from aclaf.logging import Logger, NullLogger

if TYPE_CHECKING:
    from .console import Console
    from .parser import ParseResult
    from .types import ParameterValueType


class ParameterSource(Enum):
    COMMAND_LINE = "command_line"
    DEFAULT = "default"
    CONFIG_FILE = "config_file"
    ENVIRONMENT = "environment"


ParameterSourceMapping: TypeAlias = Mapping[str, ParameterSource]


class ContextInput(TypedDict, total=False):
    command: str
    command_path: tuple[str, ...]
    parse_result: "ParseResult"
    errors: Mapping[str, tuple[str, ...]]
    parameters: Mapping[str, "ParameterValueType"]
    parameter_sources: ParameterSourceMapping
    parent: "Context"
    is_async: bool
    console: "Console"
    console_param: str
    logger: "Logger"
    context_param: str
    logger_param: str


@dataclass(slots=True, frozen=True)
class Context:
    command: str
    command_path: tuple[str, ...]
    parse_result: "ParseResult"
    errors: "Mapping[str, tuple[str, ...]]" = field(
        default_factory=lambda: MappingProxyType({})
    )
    parameters: Mapping[str, "ParameterValueType"] = field(
        default_factory=lambda: MappingProxyType({})
    )
    parameter_sources: ParameterSourceMapping = field(
        default_factory=lambda: MappingProxyType({})
    )
    parent: "Context | None" = None
    is_async: bool = False
    console: "Console" = field(default_factory=DefaultConsole)
    console_param: str | None = None
    logger: "Logger" = field(default_factory=NullLogger)
    context_param: str | None = None
    logger_param: str | None = None

    def __post_init__(self) -> None:
        for attr in ("errors", "parameters", "parameter_sources"):
            value: Mapping[str, tuple[str, ...]] | Mapping[str, ParameterValueType] = (
                cast(
                    "Mapping[str, tuple[str, ...]] | Mapping[str, ParameterValueType]",
                    getattr(self, attr),
                )
            )
            if not isinstance(value, MappingProxyType):
                object.__setattr__(
                    self,
                    attr,
                    MappingProxyType(dict(value)),
                )

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    @property
    def is_root(self) -> bool:
        return self.parent is None
