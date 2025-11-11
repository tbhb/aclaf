# Parser exceptions

--8<-- "internal.md"

Exception types raised during parsing and specification validation. This page documents all exceptions that the parser raises, including base exceptions (`ParseError`, `SpecValidationError`, `OptionError`) and specific exceptions for parsing failures such as unknown options, invalid values, and arity violations.

<!-- vale off -->

## Base exceptions

::: aclaf.parser
    options:
      heading_level: 3
      summary: false
      members:
      - ParseError
      - ParserConfigurationError
      - SpecValidationError
      - OptionError

## Option exceptions

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

## Exceptions for subcommands

::: aclaf.parser
    options:
      heading_level: 3
      summary: false
      members:
      - UnknownSubcommandError
      - AmbiguousSubcommandError

## Exceptions for positionals

::: aclaf.parser
    options:
      heading_level: 3
      summary: false
      members:
      - InsufficientPositionalArgumentsError
      - UnexpectedPositionalArgumentError

<!-- vale on -->
