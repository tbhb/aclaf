from annotated_types import Predicate

from aclaf.validation._registry import ValidatorRegistry
from aclaf.validation._shared import validate_predicate

from ._conflict import ConflictsWith, validate_conflicts_with
from ._constraint import (
    AtLeastOneOf,
    AtMostOneOf,
    ExactlyOneOf,
    MutuallyExclusive,
    validate_at_least_one_of,
    validate_at_most_one_of,
    validate_exactly_one_of,
    validate_mutually_exclusive,
)
from ._dependency import Forbids, Requires, validate_forbids, validate_requires

__all__ = [
    "AtLeastOneOf",
    "AtMostOneOf",
    "ConflictsWith",
    "ExactlyOneOf",
    "Forbids",
    "MutuallyExclusive",
    "Requires",
    "validate_at_least_one_of",
    "validate_at_most_one_of",
    "validate_conflicts_with",
    "validate_exactly_one_of",
    "validate_forbids",
    "validate_mutually_exclusive",
    "validate_requires",
]


def default_command_validators() -> "ValidatorRegistry":
    registry = ValidatorRegistry()

    # Shared validators
    registry.register(Predicate, validate_predicate)

    # Constraint validators
    registry.register(AtLeastOneOf, validate_at_least_one_of)
    registry.register(AtMostOneOf, validate_at_most_one_of)
    registry.register(ExactlyOneOf, validate_exactly_one_of)
    registry.register(MutuallyExclusive, validate_mutually_exclusive)

    # Dependency validators
    registry.register(Requires, validate_requires)
    registry.register(Forbids, validate_forbids)

    # Conflict validators
    registry.register(ConflictsWith, validate_conflicts_with)

    return registry
