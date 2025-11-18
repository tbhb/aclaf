from typing import Protocol


class BeforeMountCommandHookFunction(Protocol):
    def __call__(
        self,
    ) -> None: ...


class AfterMountCommandHookFunction(Protocol):
    def __call__(
        self,
    ) -> None: ...
