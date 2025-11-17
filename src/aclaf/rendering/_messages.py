from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Message:
    message: str


@dataclass(slots=True, frozen=True)
class SuccessMessage(Message):
    pass


@dataclass(slots=True, frozen=True)
class ErrorMessage(Message):
    pass


@dataclass(slots=True, frozen=True)
class InfoMessage(Message):
    pass


@dataclass(slots=True, frozen=True)
class WarningMessage(Message):
    pass


@dataclass(slots=True, frozen=True)
class DebugMessage(Message):
    pass


@dataclass(slots=True, frozen=True)
class StatusMessage(Message):
    pass


def success(message: str) -> SuccessMessage:
    return SuccessMessage(message=message)


def error(message: str) -> ErrorMessage:
    return ErrorMessage(message=message)


def info(message: str) -> InfoMessage:
    return InfoMessage(message=message)


def warning(message: str) -> WarningMessage:
    return WarningMessage(message=message)


def debug(message: str) -> DebugMessage:
    return DebugMessage(message=message)


def status(message: str) -> Message:
    return Message(message=message)
