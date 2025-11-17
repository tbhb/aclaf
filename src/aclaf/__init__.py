"""A command line application framework."""

from ._application import App, app
from ._command import Command, CommandInput
from ._context import Context, ParameterSource, ParameterSourceMapping
from ._conversion import ConverterFunctionType, ConverterRegistry
from ._parameters import CommandParameter, Parameter
from ._response import ConsoleResponder, ResponderProtocol
from ._runtime import (
    EMPTY_COMMAND_FUNCTION,
    CommandFunctionType,
    ParameterKind,
    RespondFunctionProtocol,
    RuntimeCommand,
    RuntimeParameter,
)
from .console import Console
from .logging import Logger
from .types import ParameterValueType
from .validators import ValidatorFunction, ValidatorRegistry

__all__ = [
    "EMPTY_COMMAND_FUNCTION",
    "App",
    "Command",
    "CommandFunctionType",
    "CommandInput",
    "CommandParameter",
    "Console",
    "ConsoleResponder",
    "Context",
    "ConverterFunctionType",
    "ConverterRegistry",
    "Logger",
    "Parameter",
    "ParameterKind",
    "ParameterSource",
    "ParameterSourceMapping",
    "ParameterValueType",
    "RespondFunctionProtocol",
    "ResponderProtocol",
    "RuntimeCommand",
    "RuntimeParameter",
    "ValidatorFunction",
    "ValidatorRegistry",
    "app",
]
