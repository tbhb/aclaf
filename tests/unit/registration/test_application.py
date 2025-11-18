import sys
from typing import TYPE_CHECKING

from aclaf.registration import App, Command, app

if TYPE_CHECKING:
    import pytest


class TestAppCreation:
    def test_app_without_name_uses_argv(
        self, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["/usr/bin/myapp", "arg1"])

        application = App()

        assert application.name == "myapp"

    def test_app_with_explicit_name(self):
        application = App(name="custom")

        assert application.name == "custom"

    def test_app_with_aliases(self):
        application = App(name="test", aliases=("t", "tst"))

        assert application.aliases == ("t", "tst")

    def test_app_with_parser_config(self):
        config = object()
        application = App(
            name="test",
            parser_config=config,  # pyright: ignore[reportArgumentType]
        )

        assert application.parser_config is config

    def test_app_is_async_flag(self):
        application = App(name="test", is_async=True)

        assert application.is_async is True

    def test_app_is_subclass_of_command(self):
        application = App(name="test")

        assert isinstance(application, Command)

    def test_app_has_no_parent_or_root(self):
        application = App(name="test")

        assert application.parent_command is None
        assert application.root_command is None

    def test_app_name_from_path_extracts_stem(
        self, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["/long/path/to/script.py", "arg"])

        application = App()

        assert application.name == "script"


class TestAppDecorator:
    def test_app_decorator_creates_app(self):
        def handler():
            pass

        result = app()(handler)  # Decorator returns the App instance
        assert isinstance(result, App)
        assert result.name == "handler"
        assert result.run_func is handler

    def test_app_decorator_with_name(self):
        @app(name="custom")
        def handler():
            pass

        result = handler
        assert result.name == "custom"

    def test_app_decorator_with_aliases(self):
        @app(aliases=("h", "hnd"))
        def handler():
            pass

        result = handler
        assert result.aliases == ("h", "hnd")

    def test_app_decorator_with_parser_config(self):
        config = object()

        @app(parser_config=config)  # pyright: ignore[reportArgumentType]
        def handler():
            pass

        result = handler
        assert result.parser_config is config

    def test_app_decorator_detects_async(self):
        @app()
        async def handler():
            pass

        result = handler
        assert result.is_async is True

    def test_app_decorator_detects_sync(self):
        @app()
        def handler():
            pass

        result = handler
        assert result.is_async is False

    def test_app_decorator_uses_function_name_if_no_name(self):
        @app()
        def my_application():
            pass

        result = my_application
        assert result.name == "my_application"

    def test_app_decorator_returns_app_instance(self):
        def original_handler():
            pass

        result = app()(original_handler)

        assert isinstance(result, App)
        assert result.run_func is original_handler
        assert result is not original_handler


class TestAppBehavior:
    def test_app_can_have_subcommands(self):
        application = App(name="test")

        @application.command()
        def sub():  # pyright: ignore[reportUnusedFunction]
            pass

        assert "sub" in application.subcommands

    def test_app_converts_to_final_command(self):
        application = App(name="test")
        application.run_func = lambda: None

        final = application.to_runtime_command()

        assert final.name == "test"
        assert final.run_func is not None

    def test_app_is_callable(self):
        application = App(name="test")
        application.run_func = lambda: None

        assert callable(application)

    def test_decorated_app_can_add_subcommands(self):
        @app()
        def main():
            pass

        @main.command()
        def sub():  # pyright: ignore[reportUnusedFunction]
            pass

        assert "sub" in main.subcommands
        assert main.subcommands["sub"].parent_command is main
