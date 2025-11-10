# Parser API

--8<-- "internal.md"

The main parser API for processing command-line arguments. This page documents the `Parser` class, which implements the complete GNU/POSIX-compliant parsing algorithm, along with the `BaseParser` abstract base class and the result data classes (`ParseResult`, `ParsedOption`, `ParsedPositional`) that represent parsed arguments.

<!-- vale off -->

::: Aclaf.parser
    options:
      members:
      - Parser
      - BaseParser
      - ParseResult
      - ParsedOption
      - ParsedPositional

<!-- vale on -->
