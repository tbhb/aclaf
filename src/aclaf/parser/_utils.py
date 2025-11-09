from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


def normalize_frozen_str_set(value: "str | Sequence[str]") -> frozenset[str]:
    if isinstance(value, frozenset):
        return value
    if isinstance(value, str):
        return frozenset((value,))
    return frozenset(value)


def full_option_name(name: str) -> str:
    if len(name) == 1:
        return f"-{name}"
    return f"--{name}"
