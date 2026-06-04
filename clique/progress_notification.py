"""
A Pub/Sub progress reporting mechanism for decoupled task monitoring.

This module provides lightweight progress signaling using the Blinker library.
It allows independent observers to track long-running operations without
entangling the core business logic with reporting components.

Tasks emit signals through :class:`ProgressNotifier`,
while observers subscribe using :class:`ProgressTracker`.
This separation keeps execution code isolated from presentation and monitoring layers.

Typical use cases include:
- Integrating external progress UIs (e.g. Click progress bars) outside the execution flow.
- Allowing multiple independent observers to react to a single task lifecycle.
- Enabling passive progress monitoring with no execution impact when unobserved.

Progress signals are emitted through a signal namespace and include ``start``, ``step``, and ``stop`` notifications.
Each signal is tagged with the current thread identifier and a user-defined label to support concurrent execution.
The label must be unique through the codebase and be consistently used by both the emitter and all registered listeners.

Classes:
    ProgressNotifier: Provides methods to notify the progress in a labeled task.
    ProgressTracker: Provides methods to track and untrack a labeled task.

Functions:
    progress_generator: Wraps an iterable to automatically emit signals during iteration.
"""

import logging
import threading
from collections.abc import Callable, Generator, Iterable
from functools import partialmethod, wraps
from typing import Any, Final, Protocol, TypeVar, runtime_checkable

from blinker import NamedSignal, Namespace

_logger = logging.getLogger(__name__)


progress = Namespace()

progress_start: Final[NamedSignal] = progress.signal('start')
progress_step: Final[NamedSignal] = progress.signal('step')
progress_stop: Final[NamedSignal] = progress.signal('stop')

T_co = TypeVar('T_co', covariant=True)


@runtime_checkable
class SizedIterable(Protocol[T_co]):
    def __iter__(self) -> Iterable[T_co]: ...

    def __len__(self) -> int: ...


def _tag_text_translator(text: str) -> str:
    return f'{threading.get_ident()}:{text}'


class ProgressNotifier:
    """
    Provide lifecycle notifications for a labeled task.

    This class acts as the publisher in the publish-subscribe pattern.
    It emits progress signals via ``notify_start``, ``notify_step``, and ``notify_stop``.

    :param label: Unique string identifier shared with trackers.
    :param length: Total number of expected steps.
    """

    def __init__(self, label: str, length: int) -> None:
        self._tag = _tag_text_translator(label)
        self._length = length
        self._active = False
        self._position = 0

    def notify_start(self) -> None:
        assert not self._active
        self._active = True
        progress_start.send(self._tag, length=self._length)

    def notify_step(self, step: int = 1) -> None:
        assert self._active
        step = min(step, self._length - self._position)
        self._position += step
        progress_step.send(self._tag, step=step, position=self._position)

    def notify_stop(self) -> None:
        assert self._active
        self._active = False
        self._position = 0
        progress_stop.send(self._tag)


class ProgressTracker:
    """
    Provide lifecycle tracking for a labeled task.

    This class acts as the subscriber in the publish-subscribe pattern.
    It registers callbacks for progress signals via ``track_start``, ``track_step``,
    and ``track_stop``. It also allows stopping observation of a task via ``untrack``.

    :param label: String identifier defined by the notifier.
    """

    def __init__(self, label: str) -> None:
        self._tag = _tag_text_translator(label)

    def _track(self, callback: Callable[..., Any], *, signal: NamedSignal) -> None:
        @wraps(callback)
        def _callback(_sender: str, *args: Any, **kwargs: Any) -> Any:
            return callback(*args, **kwargs)

        signal.connect(_callback, self._tag, weak=False)

    track_start = partialmethod(_track, signal=progress_start)
    track_step = partialmethod(_track, signal=progress_step)
    track_stop = partialmethod(_track, signal=progress_stop)

    def untrack(self) -> None:
        for progress_signal in progress.values():
            for receiver in list(progress_signal.receivers_for(self._tag)):
                progress_signal.disconnect(receiver, self._tag)


def progress_generator(iterable: Iterable[T_co], label: str) -> Generator[T_co, None, None]:
    """
    Wrap an iterable and emit progress notifications during iteration.

    :param iterable: Sized iterable object to be monitored.
    :param label: Unique string identifier used for progress signals.
    :return: A generator yielding items from the iterable.
    """
    if not isinstance(iterable, SizedIterable):
        _logger.warning(f'Ignoring notification request for "{label}": cannot apply notification for {type(iterable)}.')
        yield from iterable
        return

    progress_notifier = ProgressNotifier(label, len(iterable))
    progress_notifier.notify_start()
    for item in iterable:
        yield item
        progress_notifier.notify_step()
    progress_notifier.notify_stop()
