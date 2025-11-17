from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ErrorConfiguration:
    fuzzy_match_threshold: float = 0.6
    max_width: int = 80
    show_suggestions: bool = True
    verbosity: int = 1
