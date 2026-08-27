from collections.abc import Iterator
from os import PathLike
from types import TracebackType
from typing import Protocol, TextIO, TypedDict, TypeVar, runtime_checkable

from typing_extensions import Required

T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)


@runtime_checkable
class SizedIterable(Protocol[T_co]):
    def __iter__(self) -> Iterator[T_co]: ...

    def __len__(self) -> int: ...


class ProgressBar(Protocol[T]):
    def update(self, n_steps: int, current_item: T | None = None) -> None: ...

    def __enter__(self) -> 'ProgressBar[T]': ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...


class LogSettings(TypedDict, total=False):
    default_level: Required[int]
    stream: TextIO
    file_path: str | PathLike[str]
