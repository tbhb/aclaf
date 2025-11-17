import warnings

from aclaf.parser import CommandSpec, OptionSpec, Parser
from aclaf.parser.types import AccumulationMode, Arity


class TestBasicFlattening:
    def test_flatten_multiple_occurrences_with_varying_counts(self) -> None:
        spec = CommandSpec(
            name="build",
            options={
                "files": OptionSpec(
                    name="files",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                    flatten_values=True,
                )
            },
        )
        parser = Parser(spec=spec)

        # --files file1 file2 --files file3 --files file4 file5
        result = parser.parse(
            [
                "--files",
                "file1",
                "file2",
                "--files",
                "file3",
                "--files",
                "file4",
                "file5",
            ]
        )

        assert result.options["files"].value == (
            "file1",
            "file2",
            "file3",
            "file4",
            "file5",
        )

    def test_no_flatten_preserves_nested_structure(self) -> None:
        spec = CommandSpec(
            name="build",
            options={
                "files": OptionSpec(
                    name="files",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                    flatten_values=False,
                )
            },
        )
        parser = Parser(spec=spec)

        # --files file1 file2 --files file3
        result = parser.parse(["--files", "file1", "file2", "--files", "file3"])

        assert result.options["files"].value == (("file1", "file2"), ("file3",))

    def test_single_occurrence_same_with_or_without_flatten(self) -> None:
        # With flattening
        spec_flat = CommandSpec(
            name="build",
            options={
                "files": OptionSpec(
                    name="files",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                    flatten_values=True,
                )
            },
        )
        parser_flat = Parser(spec=spec_flat)
        result_flat = parser_flat.parse(["--files", "a", "b", "c"])

        # Without flattening
        spec_nested = CommandSpec(
            name="build",
            options={
                "files": OptionSpec(
                    name="files",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                    flatten_values=False,
                )
            },
        )
        parser_nested = Parser(spec=spec_nested)
        result_nested = parser_nested.parse(["--files", "a", "b", "c"])

        # Single occurrence with COLLECT mode and multi-value arity wraps in tuple
        # With flatten=True: the wrapper tuple is flattened away
        assert result_flat.options["files"].value == ("a", "b", "c")
        # Without flatten=False: the wrapper tuple remains
        assert result_nested.options["files"].value == (("a", "b", "c"),)

    def test_flatten_with_zero_values_per_occurrence(self) -> None:
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    name="files",
                    arity=Arity(0, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                    flatten_values=True,
                )
            },
        )
        parser = Parser(spec=spec)

        # --files a b --files --files c
        result = parser.parse(["--files", "a", "b", "--files", "--files", "c"])

        # Empty tuples from middle occurrence should be flattened away
        assert result.options["files"].value == ("a", "b", "c")

    def test_flatten_with_mixed_value_counts(self) -> None:
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    name="files",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                    flatten_values=True,
                )
            },
        )
        parser = Parser(spec=spec)

        # --files a --files b c d --files e f
        result = parser.parse(
            ["--files", "a", "--files", "b", "c", "d", "--files", "e", "f"]
        )

        assert result.options["files"].value == ("a", "b", "c", "d", "e", "f")

    def test_flatten_with_fixed_multi_value_arity(self) -> None:
        spec = CommandSpec(
            name="cmd",
            options={
                "coords": OptionSpec(
                    name="coords",
                    arity=Arity(2, 3),
                    accumulation_mode=AccumulationMode.COLLECT,
                    flatten_values=True,
                )
            },
        )
        parser = Parser(spec=spec)

        # --coords x1 y1 --coords x2 y2 z2
        result = parser.parse(["--coords", "x1", "y1", "--coords", "x2", "y2", "z2"])

        assert result.options["coords"].value == ("x1", "y1", "x2", "y2", "z2")


class TestConfigurationPrecedence:
    def test_option_level_overrides_command_level(self) -> None:
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    name="files",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                    flatten_values=True,  # Override command-level setting
                ),
                "inputs": OptionSpec(
                    name="inputs",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                    # No override, uses command-level setting
                ),
            },
            flatten_option_values=False,  # Command-level default
        )
        parser = Parser(spec=spec)

        result = parser.parse(
            [
                "--files",
                "f1",
                "f2",
                "--files",
                "f3",
                "--inputs",
                "i1",
                "i2",
                "--inputs",
                "i3",
            ]
        )

        # files should be flattened (option-level override)
        assert result.options["files"].value == ("f1", "f2", "f3")
        # inputs should be nested (command-level default)
        assert result.options["inputs"].value == (("i1", "i2"), ("i3",))

    def test_option_level_false_overrides_command_level_true(self) -> None:
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    name="files",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                    flatten_values=False,  # Explicitly disable
                ),
                "inputs": OptionSpec(
                    name="inputs",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                    # Uses command-level setting
                ),
            },
            flatten_option_values=True,  # Command-level default
        )
        parser = Parser(spec=spec)

        result = parser.parse(
            [
                "--files",
                "f1",
                "f2",
                "--files",
                "f3",
                "--inputs",
                "i1",
                "i2",
                "--inputs",
                "i3",
            ]
        )

        # files should be nested (option-level override)
        assert result.options["files"].value == (("f1", "f2"), ("f3",))
        # inputs should be flattened (command-level default)
        assert result.options["inputs"].value == ("i1", "i2", "i3")

    def test_command_level_overrides_parser_level(self) -> None:
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    name="files",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                )
            },
            flatten_option_values=True,
        )
        parser = Parser(
            spec=spec,
            flatten_option_values=False,
        )

        result = parser.parse(["--files", "f1", "f2", "--files", "f3"])

        assert result.options["files"].value == ("f1", "f2", "f3")

    def test_option_none_command_none_uses_parser_default(self) -> None:
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    name="files",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                )
            },
        )

        parser_true = Parser(spec=spec, flatten_option_values=True)
        result_true = parser_true.parse(["--files", "f1", "f2", "--files", "f3"])
        assert result_true.options["files"].value == ("f1", "f2", "f3")

        parser_false = Parser(spec=spec, flatten_option_values=False)
        result_false = parser_false.parse(["--files", "f1", "f2", "--files", "f3"])
        assert result_false.options["files"].value == (("f1", "f2"), ("f3",))

    def test_default_behavior_without_any_setting(self) -> None:
        spec = CommandSpec(
            name="cmd",
            options={
                "files": OptionSpec(
                    name="files",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                    # flatten_values defaults to None
                )
            },
            # flatten_option_values defaults to None
        )
        parser = Parser(
            spec=spec,
            # flatten_option_values defaults to False
        )

        result = parser.parse(["--files", "f1", "f2", "--files", "f3"])

        # Should be nested (default is False)
        assert result.options["files"].value == (("f1", "f2"), ("f3",))


class TestNonApplicableCases:
    def test_last_wins_mode_not_affected(self) -> None:
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")

            spec = CommandSpec(
                name="cmd",
                options={
                    "file": OptionSpec(
                        name="file",
                        arity=Arity(1, None),
                        accumulation_mode=AccumulationMode.LAST_WINS,
                        flatten_values=True,  # Has no effect (triggers warning)
                    )
                },
            )
            parser = Parser(spec=spec)

            result = parser.parse(["--file", "f1", "f2", "--file", "f3", "f4"])

            # LAST_WINS returns only the last occurrence
            assert result.options["file"].value == ("f3", "f4")

    def test_first_wins_mode_not_affected(self) -> None:
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")

            spec = CommandSpec(
                name="cmd",
                options={
                    "file": OptionSpec(
                        name="file",
                        arity=Arity(1, None),
                        accumulation_mode=AccumulationMode.FIRST_WINS,
                        flatten_values=True,  # Has no effect (triggers warning)
                    )
                },
            )
            parser = Parser(spec=spec)

            result = parser.parse(["--file", "f1", "f2", "--file", "f3", "f4"])

            # FIRST_WINS returns only the first occurrence
            assert result.options["file"].value == ("f1", "f2")

    def test_count_mode_not_affected(self) -> None:
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")

            spec = CommandSpec(
                name="cmd",
                options={
                    "verbose": OptionSpec(
                        name="verbose",
                        arity=Arity(0, 0),
                        accumulation_mode=AccumulationMode.COUNT,
                        is_flag=True,
                        flatten_values=True,  # Has no effect (triggers warning)
                    )
                },
            )
            parser = Parser(spec=spec)

            result = parser.parse(["--verbose", "--verbose", "--verbose"])

            # COUNT returns integer
            assert result.options["verbose"].value == 3

    def test_error_mode_not_affected(self) -> None:
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")

            spec = CommandSpec(
                name="cmd",
                options={
                    "file": OptionSpec(
                        name="file",
                        arity=Arity(1, None),
                        accumulation_mode=AccumulationMode.ERROR,
                        flatten_values=True,  # Has no effect (triggers warning)
                    )
                },
            )
            parser = Parser(spec=spec)

            result = parser.parse(["--file", "f1", "f2"])

            # Single occurrence
            assert result.options["file"].value == ("f1", "f2")

    def test_single_value_arity_not_affected(self) -> None:
        spec = CommandSpec(
            name="cmd",
            options={
                "file": OptionSpec(
                    name="file",
                    arity=Arity(1, 1),  # Single value per occurrence
                    accumulation_mode=AccumulationMode.COLLECT,
                    flatten_values=True,  # Has no effect (no nesting with max=1)
                )
            },
        )
        parser = Parser(spec=spec)

        result = parser.parse(["--file", "f1", "--file", "f2", "--file", "f3"])

        # Single-value COLLECT produces flat tuple automatically
        assert result.options["file"].value == ("f1", "f2", "f3")

    def test_flag_with_zero_arity_not_affected(self) -> None:
        spec = CommandSpec(
            name="cmd",
            options={
                "flag": OptionSpec(
                    name="flag",
                    arity=Arity(0, 0),
                    accumulation_mode=AccumulationMode.COLLECT,
                    is_flag=True,
                    flatten_values=True,  # Has no effect
                )
            },
        )
        parser = Parser(spec=spec)

        result = parser.parse(["--flag", "--flag", "--flag"])

        # Flags with COLLECT produce tuple of bools
        assert result.options["flag"].value == (True, True, True)


class TestValidationWarnings:
    def test_warning_when_flatten_true_with_non_collect_mode(self) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            _ = OptionSpec(
                name="file",
                arity=Arity(1, None),
                accumulation_mode=AccumulationMode.LAST_WINS,
                flatten_values=True,  # Invalid: non-COLLECT mode
            )

            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert "flatten_values=True has no effect" in str(w[0].message)
            assert "COLLECT mode" in str(w[0].message)

    def test_no_warning_when_flatten_false_with_non_collect(self) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            _ = OptionSpec(
                name="file",
                arity=Arity(1, None),
                accumulation_mode=AccumulationMode.LAST_WINS,
                flatten_values=False,  # Explicit False is fine
            )

            assert len(w) == 0

    def test_no_warning_when_flatten_none_with_non_collect(self) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            _ = OptionSpec(
                name="file",
                arity=Arity(1, None),
                accumulation_mode=AccumulationMode.LAST_WINS,
                flatten_values=None,  # Inherited, no warning
            )

            assert len(w) == 0

    def test_no_warning_when_flatten_true_with_collect_mode(self) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            _ = OptionSpec(
                name="file",
                arity=Arity(1, None),
                accumulation_mode=AccumulationMode.COLLECT,
                flatten_values=True,  # Valid configuration
            )

            assert len(w) == 0


class TestInteractionWithOtherOptions:
    def test_flatten_only_affects_specified_options(self) -> None:
        spec = CommandSpec(
            name="cmd",
            options={
                "flat": OptionSpec(
                    name="flat",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                    flatten_values=True,
                ),
                "nested": OptionSpec(
                    name="nested",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                    flatten_values=False,
                ),
                "single": OptionSpec(
                    name="single",
                    arity=Arity(1, 1),
                    accumulation_mode=AccumulationMode.LAST_WINS,
                ),
            },
        )
        parser = Parser(spec=spec)

        result = parser.parse(
            [
                "--flat",
                "f1",
                "f2",
                "--flat",
                "f3",
                "--nested",
                "n1",
                "n2",
                "--nested",
                "n3",
                "--single",
                "s1",
            ]
        )

        assert result.options["flat"].value == ("f1", "f2", "f3")
        assert result.options["nested"].value == (("n1", "n2"), ("n3",))
        assert result.options["single"].value == "s1"

    def test_large_number_of_occurrences(self) -> None:
        spec = CommandSpec(
            name="cmd",
            options={
                "items": OptionSpec(
                    name="items",
                    arity=Arity(1, None),
                    accumulation_mode=AccumulationMode.COLLECT,
                    flatten_values=True,
                )
            },
        )
        parser = Parser(spec=spec)

        # Generate 100 occurrences with varying value counts
        args: list[str] = []
        expected: list[str] = []
        for i in range(100):
            args.extend(["--items", f"item{i}"])
            expected.append(f"item{i}")

        result = parser.parse(args)

        value = result.options["items"].value
        assert value == tuple(expected)
        assert isinstance(value, tuple)
        assert len(value) == 100
