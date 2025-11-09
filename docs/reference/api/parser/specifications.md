# Parser Specifications API

Specification types for defining command structure and behavior. This page documents the specification classes (CommandSpec, OptionSpec, PositionalSpec) used to define commands, options, and positional arguments, along with supporting types like Arity and AccumulationMode that control parsing behavior.

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
