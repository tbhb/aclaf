"""Unit tests for string parameter validators."""

import re

import pytest

from aclaf.validation.parameter._string import (
    Alpha,
    Alphanumeric,
    Choices,
    Contains,
    EndsWith,
    Lowercase,
    NotBlank,
    Numeric,
    Pattern,
    Printable,
    StartsWith,
    StringValidations,
    Uppercase,
    validate_alpha,
    validate_alphanumeric,
    validate_choices,
    validate_contains,
    validate_ends_with,
    validate_lowercase,
    validate_not_blank,
    validate_numeric,
    validate_pattern,
    validate_printable,
    validate_starts_with,
    validate_uppercase,
)


class TestValidateNotBlank:
    def test_validates_non_blank_string(self):
        metadata = NotBlank()
        value = "hello"

        result = validate_not_blank(value, metadata)

        assert result is None

    def test_returns_error_for_blank_string(self):
        metadata = NotBlank()
        value = "   "

        result = validate_not_blank(value, metadata)

        assert result == ("must not be blank.",)

    def test_returns_error_for_empty_string(self):
        metadata = NotBlank()
        value = ""

        result = validate_not_blank(value, metadata)

        assert result == ("must not be blank.",)

    def test_validates_string_with_content(self):
        metadata = NotBlank()
        value = "  content  "

        result = validate_not_blank(value, metadata)

        assert result is None

    def test_validates_multiline_string(self):
        metadata = NotBlank()
        value = "\n\n  text  \n\n"

        result = validate_not_blank(value, metadata)

        assert result is None


class TestValidatePattern:
    def test_validates_matching_pattern(self):
        metadata = Pattern(pattern=r"^\d{3}-\d{3}-\d{4}$")
        value = "123-456-7890"

        result = validate_pattern(value, metadata)

        assert result is None

    def test_returns_error_for_non_matching_pattern(self):
        metadata = Pattern(pattern=r"^\d{3}-\d{3}-\d{4}$")
        value = "not a phone"

        result = validate_pattern(value, metadata)

        assert result == (r"must match pattern '^\d{3}-\d{3}-\d{4}$'.",)

    def test_validates_email_pattern(self):
        metadata = Pattern(pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        value = "test@example.com"

        result = validate_pattern(value, metadata)

        assert result is None

    def test_validates_simple_pattern(self):
        metadata = Pattern(pattern=r"^hello")
        value = "hello world"

        result = validate_pattern(value, metadata)

        assert result is None

    def test_raises_exception_for_invalid_regex(self):
        metadata = Pattern(pattern=r"[invalid(")
        value = "test"

        with pytest.raises(re.PatternError):
            _ = validate_pattern(value, metadata)


class TestValidateChoices:
    def test_validates_value_in_choices(self):
        metadata = Choices(choices=("red", "green", "blue"))
        value = "red"

        result = validate_choices(value, metadata)

        assert result is None

    def test_returns_error_for_invalid_choice(self):
        metadata = Choices(choices=("red", "green", "blue"))
        value = "yellow"

        result = validate_choices(value, metadata)

        assert result == ("must be one of 'red', 'green', 'blue'.",)

    def test_validates_single_choice(self):
        metadata = Choices(choices=("only",))
        value = "only"

        result = validate_choices(value, metadata)

        assert result is None

    def test_validates_numeric_string_choices(self):
        metadata = Choices(choices=("1", "2", "3"))
        value = "2"

        result = validate_choices(value, metadata)

        assert result is None


class TestValidateStartsWith:
    def test_validates_string_with_prefix(self):
        metadata = StartsWith(prefix="hello")
        value = "hello world"

        result = validate_starts_with(value, metadata)

        assert result is None

    def test_returns_error_for_string_without_prefix(self):
        metadata = StartsWith(prefix="hello")
        value = "goodbye world"

        result = validate_starts_with(value, metadata)

        assert result == ("must start with 'hello'.",)

    def test_validates_exact_match(self):
        metadata = StartsWith(prefix="test")
        value = "test"

        result = validate_starts_with(value, metadata)

        assert result is None

    def test_validates_empty_prefix(self):
        metadata = StartsWith(prefix="")
        value = "anything"

        result = validate_starts_with(value, metadata)

        assert result is None

    def test_validates_case_sensitive_prefix(self):
        metadata = StartsWith(prefix="Hello")
        value = "Hello World"

        result = validate_starts_with(value, metadata)

        assert result is None


class TestValidateEndsWith:
    def test_validates_string_with_suffix(self):
        metadata = EndsWith(suffix="world")
        value = "hello world"

        result = validate_ends_with(value, metadata)

        assert result is None

    def test_returns_error_for_string_without_suffix(self):
        metadata = EndsWith(suffix="world")
        value = "hello universe"

        result = validate_ends_with(value, metadata)

        assert result == ("must end with 'world'.",)

    def test_validates_exact_match(self):
        metadata = EndsWith(suffix="test")
        value = "test"

        result = validate_ends_with(value, metadata)

        assert result is None

    def test_validates_empty_suffix(self):
        metadata = EndsWith(suffix="")
        value = "anything"

        result = validate_ends_with(value, metadata)

        assert result is None

    def test_validates_file_extension(self):
        metadata = EndsWith(suffix=".txt")
        value = "document.txt"

        result = validate_ends_with(value, metadata)

        assert result is None


class TestValidateContains:
    def test_validates_string_containing_substring(self):
        metadata = Contains(substring="world")
        value = "hello world today"

        result = validate_contains(value, metadata)

        assert result is None

    def test_returns_error_for_string_without_substring(self):
        metadata = Contains(substring="world")
        value = "hello universe"

        result = validate_contains(value, metadata)

        assert result == ("must contain 'world'.",)

    def test_validates_substring_at_start(self):
        metadata = Contains(substring="hello")
        value = "hello world"

        result = validate_contains(value, metadata)

        assert result is None

    def test_validates_substring_at_end(self):
        metadata = Contains(substring="world")
        value = "hello world"

        result = validate_contains(value, metadata)

        assert result is None

    def test_validates_exact_match(self):
        metadata = Contains(substring="test")
        value = "test"

        result = validate_contains(value, metadata)

        assert result is None


class TestValidateLowercase:
    def test_validates_lowercase_string(self):
        metadata = Lowercase()
        value = "hello world"

        result = validate_lowercase(value, metadata)

        assert result is None

    def test_returns_error_for_uppercase_string(self):
        metadata = Lowercase()
        value = "HELLO WORLD"

        result = validate_lowercase(value, metadata)

        assert result == ("must be lowercase.",)

    def test_returns_error_for_mixed_case(self):
        metadata = Lowercase()
        value = "Hello World"

        result = validate_lowercase(value, metadata)

        assert result == ("must be lowercase.",)

    def test_validates_lowercase_with_numbers(self):
        metadata = Lowercase()
        value = "hello123"

        result = validate_lowercase(value, metadata)

        assert result is None

    def test_validates_lowercase_with_special_chars(self):
        metadata = Lowercase()
        value = "hello-world_123"

        result = validate_lowercase(value, metadata)

        assert result is None


class TestValidateUppercase:
    def test_validates_uppercase_string(self):
        metadata = Uppercase()
        value = "HELLO WORLD"

        result = validate_uppercase(value, metadata)

        assert result is None

    def test_returns_error_for_lowercase_string(self):
        metadata = Uppercase()
        value = "hello world"

        result = validate_uppercase(value, metadata)

        assert result == ("must be uppercase.",)

    def test_returns_error_for_mixed_case(self):
        metadata = Uppercase()
        value = "Hello World"

        result = validate_uppercase(value, metadata)

        assert result == ("must be uppercase.",)

    def test_validates_uppercase_with_numbers(self):
        metadata = Uppercase()
        value = "HELLO123"

        result = validate_uppercase(value, metadata)

        assert result is None

    def test_validates_uppercase_with_special_chars(self):
        metadata = Uppercase()
        value = "HELLO-WORLD_123"

        result = validate_uppercase(value, metadata)

        assert result is None


class TestValidateAlphanumeric:
    def test_validates_alphanumeric_string(self):
        metadata = Alphanumeric()
        value = "hello123"

        result = validate_alphanumeric(value, metadata)

        assert result is None

    def test_returns_error_for_string_with_special_chars(self):
        metadata = Alphanumeric()
        value = "hello-world"

        result = validate_alphanumeric(value, metadata)

        assert result == ("must be alphanumeric (letters and numbers only).",)

    def test_validates_only_letters(self):
        metadata = Alphanumeric()
        value = "hello"

        result = validate_alphanumeric(value, metadata)

        assert result is None

    def test_validates_only_numbers(self):
        metadata = Alphanumeric()
        value = "123456"

        result = validate_alphanumeric(value, metadata)

        assert result is None

    def test_returns_error_for_spaces(self):
        metadata = Alphanumeric()
        value = "hello world"

        result = validate_alphanumeric(value, metadata)

        assert result == ("must be alphanumeric (letters and numbers only).",)


class TestValidateAlpha:
    def test_validates_alphabetic_string(self):
        metadata = Alpha()
        value = "hello"

        result = validate_alpha(value, metadata)

        assert result is None

    def test_returns_error_for_numeric_string(self):
        metadata = Alpha()
        value = "hello123"

        result = validate_alpha(value, metadata)

        assert result == ("must be alphabetic (letters only).",)

    def test_returns_error_for_special_chars(self):
        metadata = Alpha()
        value = "hello-world"

        result = validate_alpha(value, metadata)

        assert result == ("must be alphabetic (letters only).",)

    def test_validates_mixed_case_alpha(self):
        metadata = Alpha()
        value = "HelloWorld"

        result = validate_alpha(value, metadata)

        assert result is None

    def test_returns_error_for_spaces(self):
        metadata = Alpha()
        value = "hello world"

        result = validate_alpha(value, metadata)

        assert result == ("must be alphabetic (letters only).",)


class TestValidateNumeric:
    def test_validates_numeric_string(self):
        metadata = Numeric()
        value = "123456"

        result = validate_numeric(value, metadata)

        assert result is None

    def test_returns_error_for_alphabetic_string(self):
        metadata = Numeric()
        value = "hello"

        result = validate_numeric(value, metadata)

        assert result == ("must be numeric (numbers only).",)

    def test_returns_error_for_alphanumeric(self):
        metadata = Numeric()
        value = "abc123"

        result = validate_numeric(value, metadata)

        assert result == ("must be numeric (numbers only).",)

    def test_validates_zero(self):
        metadata = Numeric()
        value = "0"

        result = validate_numeric(value, metadata)

        assert result is None

    def test_returns_error_for_decimal(self):
        metadata = Numeric()
        value = "123.45"

        result = validate_numeric(value, metadata)

        assert result == ("must be numeric (numbers only).",)


class TestValidatePrintable:
    def test_validates_printable_string(self):
        metadata = Printable()
        value = "hello world 123"

        result = validate_printable(value, metadata)

        assert result is None

    def test_returns_error_for_non_printable(self):
        metadata = Printable()
        value = "hello\x00world"

        result = validate_printable(value, metadata)

        assert result == ("must contain only printable characters.",)

    def test_validates_string_with_special_chars(self):
        metadata = Printable()
        value = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"

        result = validate_printable(value, metadata)

        assert result is None

    def test_validates_empty_string(self):
        metadata = Printable()
        value = ""

        result = validate_printable(value, metadata)

        assert result is None

    def test_returns_error_for_control_chars(self):
        metadata = Printable()
        value = "hello\nworld\ttab"

        result = validate_printable(value, metadata)

        assert result == ("must contain only printable characters.",)


class TestStringValidations:
    def test_iterates_not_blank_validation(self):
        metadata = StringValidations(not_blank=True)

        validators = list(metadata)

        assert len(validators) == 1
        assert isinstance(validators[0], NotBlank)

    def test_iterates_pattern_validation(self):
        metadata = StringValidations(pattern=r"^\d+$")

        validators = list(metadata)

        assert len(validators) == 1
        assert isinstance(validators[0], Pattern)
        assert validators[0].pattern == r"^\d+$"

    def test_iterates_choices_validation(self):
        metadata = StringValidations(choices=("a", "b", "c"))

        validators = list(metadata)

        assert len(validators) == 1
        assert isinstance(validators[0], Choices)
        assert validators[0].choices == ("a", "b", "c")

    def test_iterates_starts_with_validation(self):
        metadata = StringValidations(starts_with="prefix")

        validators = list(metadata)

        assert len(validators) == 1
        assert isinstance(validators[0], StartsWith)
        assert validators[0].prefix == "prefix"

    def test_iterates_ends_with_validation(self):
        metadata = StringValidations(ends_with="suffix")

        validators = list(metadata)

        assert len(validators) == 1
        assert isinstance(validators[0], EndsWith)
        assert validators[0].suffix == "suffix"

    def test_iterates_contains_validation(self):
        metadata = StringValidations(contains="substring")

        validators = list(metadata)

        assert len(validators) == 1
        assert isinstance(validators[0], Contains)
        assert validators[0].substring == "substring"

    def test_iterates_lowercase_validation(self):
        metadata = StringValidations(lowercase=True)

        validators = list(metadata)

        assert len(validators) == 1
        assert isinstance(validators[0], Lowercase)

    def test_iterates_uppercase_validation(self):
        metadata = StringValidations(uppercase=True)

        validators = list(metadata)

        assert len(validators) == 1
        assert isinstance(validators[0], Uppercase)

    def test_iterates_alphanumeric_validation(self):
        metadata = StringValidations(alphanumeric=True)

        validators = list(metadata)

        assert len(validators) == 1
        assert isinstance(validators[0], Alphanumeric)

    def test_iterates_alpha_validation(self):
        metadata = StringValidations(alpha=True)

        validators = list(metadata)

        assert len(validators) == 1
        assert isinstance(validators[0], Alpha)

    def test_iterates_numeric_validation(self):
        metadata = StringValidations(numeric=True)

        validators = list(metadata)

        assert len(validators) == 1
        assert isinstance(validators[0], Numeric)

    def test_iterates_printable_validation(self):
        metadata = StringValidations(printable=True)

        validators = list(metadata)

        assert len(validators) == 1
        assert isinstance(validators[0], Printable)

    def test_iterates_multiple_validations(self):
        metadata = StringValidations(
            not_blank=True,
            pattern=r"^\w+$",
            lowercase=True,
            alphanumeric=True,
        )

        validators = list(metadata)

        assert len(validators) == 4
        assert isinstance(validators[0], NotBlank)
        assert isinstance(validators[1], Pattern)
        assert isinstance(validators[2], Lowercase)
        assert isinstance(validators[3], Alphanumeric)

    def test_skips_false_boolean_validations(self):
        metadata = StringValidations(
            not_blank=False,
            lowercase=False,
            uppercase=False,
        )

        validators = list(metadata)

        assert len(validators) == 0

    def test_skips_none_string_validations(self):
        metadata = StringValidations(
            pattern=None,
            choices=None,
            starts_with=None,
            ends_with=None,
            contains=None,
        )

        validators = list(metadata)

        assert len(validators) == 0

    def test_iterates_all_validations(self):
        metadata = StringValidations(
            not_blank=True,
            pattern=r"test",
            choices=("a", "b"),
            starts_with="pre",
            ends_with="suf",
            contains="mid",
            lowercase=True,
            uppercase=True,
            alphanumeric=True,
            alpha=True,
            numeric=True,
            printable=True,
        )

        validators = list(metadata)

        assert len(validators) == 12
