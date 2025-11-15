from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import TypeAlias, cast

from annotated_types import BaseMetadata, Ge, Gt, Le, Lt, MaxLen, MinLen, MultipleOf

from aclaf._types import ParameterValueType
from aclaf.logging import Logger, NullLogger

ParameterValidatorFunctionType: TypeAlias = Callable[
    [ParameterValueType | None, Mapping[str, ParameterValueType | None], BaseMetadata],
    tuple[str, ...] | None,
]

ParameterSetValidatorFunctionType: TypeAlias = Callable[
    [Mapping[str, ParameterValueType | None]], Mapping[str, tuple[str, ...]] | None
]


ValidatorRegistryKey: TypeAlias = type[BaseMetadata]


@dataclass(slots=True)
class ParameterValidatorRegistry:
    logger: Logger = field(default_factory=NullLogger)
    _validators: dict[ValidatorRegistryKey, ParameterValidatorFunctionType] = field(
        default_factory=dict, init=False, repr=False
    )

    def register(
        self,
        key: ValidatorRegistryKey,
        validator: ParameterValidatorFunctionType,
    ) -> None:
        if key in self._validators:
            msg = f"Validator for key '{key.__name__}' is already registered."
            raise ValueError(msg)
        self._validators[key] = validator

    def unregister(self, key: ValidatorRegistryKey) -> None:
        del self._validators[key]

    def get_validator(
        self,
        key: ValidatorRegistryKey,
    ) -> ParameterValidatorFunctionType | None:
        return self._validators.get(key)

    def has_validator(self, key: ValidatorRegistryKey) -> bool:
        return key in self._validators

    def validate(
        self,
        value: ParameterValueType | None,
        other_parameters: Mapping[str, ParameterValueType | None],
        metadata: tuple[BaseMetadata, ...],
    ) -> tuple[str, ...] | None:
        errors: list[str] = []

        for meta in metadata:
            validator = self.get_validator(type(meta))
            if validator is not None:
                validator_errors = validator(value, other_parameters, meta)
                if validator_errors:
                    errors.extend(validator_errors)

        if errors:
            return tuple(errors)
        return None

    def _make_default_validators(self) -> None:
        self.register(Gt, validate_gt)
        self.register(Ge, validate_ge)
        self.register(Lt, validate_lt)
        self.register(Le, validate_le)
        self.register(MultipleOf, validate_multiple_of)
        self.register(MinLen, validate_min_len)
        self.register(MaxLen, validate_max_len)


def validate_gt(
    value: ParameterValueType | None,
    _other_parameters: Mapping[str, ParameterValueType | None],
    metadata: BaseMetadata,
) -> tuple[str, ...] | None:
    metadata = cast("Gt", metadata)
    errors: list[str] = []
    try:
        if not value > metadata.gt:  # pyright: ignore[reportOperatorIssue]
            errors.append(f"must be greater than {metadata.gt}.")
    except TypeError:
        errors.append(f"cannot be compared with {metadata.gt}.")

    if errors:
        return tuple(errors)
    return None


def validate_ge(
    value: ParameterValueType | None,
    _other_parameters: Mapping[str, ParameterValueType | None],
    metadata: BaseMetadata,
) -> tuple[str, ...] | None:
    metadata = cast("Ge", metadata)
    errors: list[str] = []
    try:
        if not value >= metadata.ge:  # pyright: ignore[reportOperatorIssue]
            errors.append(f"must be greater than or equal to {metadata.ge}.")
    except TypeError:
        errors.append(f"cannot be compared with {metadata.ge}.")

    if errors:
        return tuple(errors)
    return None


def validate_lt(
    value: ParameterValueType | None,
    _other_parameters: Mapping[str, ParameterValueType | None],
    metadata: BaseMetadata,
) -> tuple[str, ...] | None:
    metadata = cast("Lt", metadata)
    errors: list[str] = []
    try:
        if not value < metadata.lt:  # pyright: ignore[reportOperatorIssue]
            errors.append(f"must be less than {metadata.lt}.")
    except TypeError:
        errors.append(f"cannot be compared with {metadata.lt}.")

    if errors:
        return tuple(errors)
    return None


def validate_le(
    value: ParameterValueType | None,
    _other_parameters: Mapping[str, ParameterValueType | None],
    metadata: BaseMetadata,
) -> tuple[str, ...] | None:
    metadata = cast("Le", metadata)
    errors: list[str] = []
    try:
        if not value <= metadata.le:  # pyright: ignore[reportOperatorIssue]
            errors.append(f"must be less than or equal to {metadata.le}.")
    except TypeError:
        errors.append(f"cannot be compared with {metadata.le}.")

    if errors:
        return tuple(errors)
    return None


def validate_multiple_of(
    value: ParameterValueType | None,
    _other_parameters: Mapping[str, ParameterValueType | None],
    metadata: BaseMetadata,
) -> tuple[str, ...] | None:
    metadata = cast("MultipleOf", metadata)
    errors: list[str] = []
    try:
        if (value % metadata.multiple_of) != 0:  # pyright: ignore[reportOperatorIssue]
            errors.append(f"must be a multiple of {metadata.multiple_of}.")
    except TypeError:
        errors.append(f"cannot be divided by {metadata.multiple_of}.")

    if errors:
        return tuple(errors)
    return None


def validate_min_len(
    value: ParameterValueType | None,
    _other_parameters: Mapping[str, ParameterValueType | None],
    metadata: BaseMetadata,
) -> tuple[str, ...] | None:
    metadata = cast("MinLen", metadata)
    errors: list[str] = []
    try:
        if len(value) < metadata.min_length:  # pyright: ignore[reportArgumentType]
            errors.append(f"length must be at least {metadata.min_length}.")
    except TypeError:
        errors.append("length cannot be determined.")

    if errors:
        return tuple(errors)
    return None


def validate_max_len(
    value: ParameterValueType | None,
    _other_parameters: Mapping[str, ParameterValueType | None],
    metadata: BaseMetadata,
) -> tuple[str, ...] | None:
    metadata = cast("MaxLen", metadata)
    errors: list[str] = []
    try:
        if len(value) > metadata.max_length:  # pyright: ignore[reportArgumentType]
            errors.append(f"length must be at most {metadata.max_length}.")
    except TypeError:
        errors.append("length cannot be determined.")

    if errors:
        return tuple(errors)
    return None
