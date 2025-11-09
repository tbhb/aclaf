# Parser Exceptions

Exception types raised during parsing and specification validation. This page documents all exceptions that can be raised by the parser, including base exceptions (ParseError, SpecValidationError, OptionError) and specific exceptions for various parsing failures such as unknown options, invalid values, and arity violations.

## Base Exceptions

::: aclaf.parser
    options:
      heading_level: 3
      summary: false
      members:
      - ParseError
      - SpecValidationError
      - OptionError

## Option Exceptions

::: aclaf.parser
    options:
      heading_level: 3
      summary: false
      members:
      - UnknownOptionError
      - AmbiguousOptionError
      - OptionCannotBeSpecifiedMultipleTimesError
      - OptionDoesNotAcceptValueError
      - FlagWithValueError
      - InvalidFlagValueError
      - InsufficientOptionValuesError

## Subcommand Exceptions

::: aclaf.parser
    options:
      heading_level: 3
      summary: false
      members:
      - UnknownSubcommandError
      - AmbiguousSubcommandError

## Positional Exceptions

::: aclaf.parser
    options:
      heading_level: 3
      summary: false
      members:
      - InsufficientPositionalArgumentsError
      - UnexpectedPositionalArgumentError
