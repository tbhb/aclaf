"""Validator re-exports from annotated-types for convenience.

This module re-exports commonly used validators from annotated-types to provide
a convenient import location for users of the framework. The actual validation
logic is implemented in aclaf._validation.
"""

from ._registry import (
    ValidatorFunction,
    ValidatorMetadataType,
    ValidatorRegistry,
    ValidatorRegistryKey,
)
from ._shared import validate_predicate
from .command import default_command_validators
from .parameter import default_parameter_validators

__all__ = [
    "ValidatorFunction",
    "ValidatorMetadataType",
    "ValidatorRegistry",
    "ValidatorRegistryKey",
    "default_command_validators",
    "default_parameter_validators",
    "validate_predicate",
]
