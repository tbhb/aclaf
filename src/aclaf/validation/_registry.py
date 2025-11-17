from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, TypeAlias

from annotated_types import BaseMetadata, GroupedMetadata

from aclaf.logging import NullLogger

if TYPE_CHECKING:
    from aclaf.logging import Logger
    from aclaf.types import ParameterValueMappingType, ParameterValueType


ValidatorMetadataType: TypeAlias = BaseMetadata | GroupedMetadata


class ValidatorFunction(Protocol):
    def __call__(
        self,
        value: "ParameterValueType | ParameterValueMappingType | None",
        metadata: ValidatorMetadataType,
    ) -> tuple[str, ...] | None: ...


ValidatorRegistryKey: TypeAlias = type[BaseMetadata] | type[GroupedMetadata]


@dataclass(slots=True)
class ValidatorRegistry:
    logger: "Logger" = field(default_factory=NullLogger)
    validators: dict[ValidatorRegistryKey, ValidatorFunction] = field(
        default_factory=dict, init=False, repr=False
    )

    def register(
        self,
        key: ValidatorRegistryKey,
        validator: ValidatorFunction,
    ) -> None:
        if key in self.validators:
            msg = f"Validator for key '{key.__name__}' is already registered."
            raise ValueError(msg)
        self.validators[key] = validator

    def unregister(self, key: ValidatorRegistryKey) -> None:
        del self.validators[key]

    def get_validator(
        self,
        key: ValidatorRegistryKey,
    ) -> ValidatorFunction | None:
        return self.validators.get(key)

    def has_validator(self, key: ValidatorRegistryKey) -> bool:
        return key in self.validators

    def validate(
        self,
        value: "ParameterValueType | ParameterValueMappingType | None",
        metadata: tuple[ValidatorMetadataType, ...],
    ) -> tuple[str, ...] | None:
        errors: list[str] = []

        for meta in metadata:
            validator = self.get_validator(type(meta))
            if validator is not None:
                validator_errors = validator(value, meta)
                if validator_errors:
                    errors.extend(validator_errors)

        if errors:
            return tuple(errors)
        return None
