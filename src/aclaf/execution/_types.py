from collections.abc import Callable, Mapping
from enum import IntEnum, auto

from aclaf.response import AsyncResponseType, SyncResponseType
from aclaf.types import ParameterValueType

DefaultFactoryFunction = Callable[..., ParameterValueType]

SyncCommandFunctionType = Callable[..., SyncResponseType]
AsyncCommandFunctionType = Callable[..., AsyncResponseType]

CommandFunctionType = SyncCommandFunctionType | AsyncCommandFunctionType


class ParameterSource(IntEnum):
    COMMAND_LINE = auto()
    DEFAULT = auto()
    CONFIG_FILE = auto()
    ENVIRONMENT = auto()


ParameterSourceMapping = Mapping[str, ParameterSource]
