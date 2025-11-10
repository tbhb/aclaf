# Parser specifications API

--8<-- "internal.md"

Specification types for defining command structure and behavior. This page documents the specification classes (`CommandSpec`, `OptionSpec`, `PositionalSpec`) used to define commands, options, and positional arguments, along with supporting types like `arity` and `AccumulationMode` that control parsing behavior.

<!-- vale off -->

::: aclaf.parser
    options:
      members:
      - CommandSpec
      - OptionSpec
      - PositionalSpec
      - AccumulationMode
      - Arity
      - EXACTLY_ONE_ARITY
      - ONE_OR_MORE_ARITY
      - ZERO_ARITY
      - ZERO_OR_MORE_ARITY
      - ZERO_OR_ONE_ARITY

<!-- vale on -->
