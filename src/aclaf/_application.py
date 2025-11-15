import sys
from pathlib import Path
from typing import TYPE_CHECKING

from aclaf._runtime import is_async_command_function
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
        is_async: bool = False,
        logger: "Logger | str | None" = None,
        parser_config: "ParserConfiguration | None" = None,
    ) -> None:
        name = name or Path(sys.argv[0]).stem
        logger = create_logger(logger, name=name)
        super().__init__(
            name=name,
            aliases=aliases or (),
            parser_config=parser_config,
            is_async=is_async,
            logger=logger or NullLogger(),
        )


def app(
    name: str | None = None,
    *,
    aliases: "Iterable[str] | None" = None,
    logger: "Logger | str | None" = None,
    parser_config: "ParserConfiguration | None" = None,
) -> "Callable[[CommandFunctionType], Command]":
    def decorator(
        func: "CommandFunctionType",
    ) -> "Command":
        app_name = name or func.__name__
        app_logger = create_logger(logger, name=app_name)
        is_async = is_async_command_function(func)
        app = App(
            name=app_name,
            aliases=aliases,
            parser_config=parser_config,
            is_async=is_async,
            logger=app_logger,
        )
        app.run_func = func
        return app

    return decorator
