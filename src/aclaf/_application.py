import sys
from pathlib import Path
from typing import TYPE_CHECKING

from aclaf._parameters import extract_function_parameters
from aclaf._runtime import is_async_command_function
from aclaf.console import Console, DefaultConsole
from aclaf.logging import Logger, NullLogger, create_logger

from ._command import Command

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from ._runtime import CommandFunctionType
    from .parser import ParserConfiguration


class App(Command):
    def __init__(
        self,
        name: str | None = None,
        *,
        aliases: "Iterable[str] | None" = None,
        console: "Console | None" = None,
        is_async: bool = False,
        logger: "Logger | str | None" = None,
        parser_config: "ParserConfiguration | None" = None,
    ) -> None:
        name = name or Path(sys.argv[0]).stem
        logger = create_logger(logger, name=name)
        super().__init__(
            name=name,
            aliases=aliases or (),
            console=console or DefaultConsole(),
            parser_config=parser_config,
            is_async=is_async,
            logger=logger or NullLogger(),
        )


def app(
    name: str | None = None,
    *,
    aliases: "Iterable[str] | None" = None,
    console: "Console | None" = None,
    logger: "Logger | str | None" = None,
    parser_config: "ParserConfiguration | None" = None,
) -> "Callable[[CommandFunctionType], Command]":
    def decorator(
        func: "CommandFunctionType",
    ) -> "Command":
        is_async = is_async_command_function(func)
        app = App(
            name=name,
            aliases=aliases,
            parser_config=parser_config,
            is_async=is_async,
            logger=logger,
            console=console,
        )
        parameters, special_parameters = extract_function_parameters(func)
        app.parameters = parameters
        app.context_param = special_parameters.get("context")
        app.console_param = special_parameters.get("console")
        app.logger_param = special_parameters.get("logger")
        app.run_func = func
        return app

    return decorator
