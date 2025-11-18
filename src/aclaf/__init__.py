"""A command line application framework."""

from ._application import App, app
from .console import Console
from .conversion import ConverterFunctionType, ConverterRegistry
from .execution import (
    EMPTY_COMMAND_FUNCTION,
    CommandFunctionType,
    Context,
    ParameterSource,
    ParameterSourceMapping,
    RuntimeCommand,
    RuntimeParameter,
)
from .logging import Logger
from .registration import Command, CommandInput, CommandParameter, Parameter
from .types import ParameterKind, ParameterValueType
from .validation import ValidatorFunction, ValidatorRegistry

__all__ = [
    "EMPTY_COMMAND_FUNCTION",
    "App",
    "Command",
    "CommandFunctionType",
    "CommandInput",
    "CommandParameter",
    "Console",
    "Context",
    "ConverterFunctionType",
    "ConverterRegistry",
    "Logger",
    "Parameter",
    "ParameterKind",
    "ParameterSource",
    "ParameterSourceMapping",
    "ParameterValueType",
    "RuntimeCommand",
    "RuntimeParameter",
    "ValidatorFunction",
    "ValidatorRegistry",
    "app",
]
