from collections.abc import Iterator
from contextlib import contextmanager
from functools import partial
from string import Template
from typing import Any

import click
from click import Context, get_current_context
from click import progressbar as create_progressbar

from ._typing import ProgressBar
from .exceptions import LeaderException
from .progress_notification import ProgressTracker


class Leader:
    """
    TBD

    :param message_templates:
    :param args:
    :param kwargs:
    """

    def __init__(self, message_templates: dict[str, str] | None = None, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._message_templates: dict[str, str] = message_templates if message_templates is not None else {}
        self._progressbar_factory = create_progressbar
        self._progressbar_attr_name = '__progressbar__'

    @property
    def attrs(self) -> dict[str, Any]:
        return {}

    @property
    def ctx(self) -> Context | None:
        return get_current_context(silent=True)

    @property
    def ctx_progressbar(self) -> ProgressBar[Any] | None:
        return getattr(self.ctx, self._progressbar_attr_name, None)

    @ctx_progressbar.setter
    def ctx_progressbar(self, progressbar: ProgressBar[Any] | None) -> None:
        assert self.ctx
        setattr(self.ctx, self._progressbar_attr_name, progressbar)

    def invoke(self, *args: Any, **kwargs: Any) -> None:
        """
        TBD

        :param args:
        :param kwargs:
        """
        pass

    def _echo(self, *args: Any, **kwargs: Any) -> None:  # noqa: PLR6301
        """
        TBD

        :param args:
        :param kwargs:
        """
        click.secho(*args, **kwargs)

    def send_message(
        self, text: str | None = None, key: str | None = None, values: dict[str, str] | None = None, **kwargs: Any
    ) -> None:
        """
        TBD

        :param text:
        :param key:
        :param values:
        :param kwargs:
        """
        if key:
            if text:
                raise LeaderException('Cannot mix raw text and template key')
            if template := self._message_templates.get(key):
                text = Template(template).safe_substitute(**values) if values else template

        if not text:
            return
        self._echo(text, **kwargs)

    def _start_progressbar(self, label: str, length: int) -> None:
        if self.ctx_progressbar is not None:
            raise LeaderException('Cannot raise several progress bars simultaneously')

        self.ctx_progressbar = self._progressbar_factory(label=label, length=length)
        self.ctx_progressbar.__enter__()  # pylint: disable=unnecessary-dunder-call

    def _update_progressbar(self, step: int, position: int) -> None:
        if self.ctx_progressbar is None:
            raise LeaderException('Cannot find ProgressBar object for updating')

        self.ctx_progressbar.update(step, position)

    def _end_progressbar(self) -> None:
        if self.ctx_progressbar is None:
            raise LeaderException('Cannot find ProgressBar object for stopping')

        self.ctx_progressbar.__exit__(None, None, None)
        self.ctx_progressbar = None

    @contextmanager
    def progress_notification(self, label: str) -> Iterator[None]:
        """
        TBD

        :param label:
        """
        if not self.ctx:
            raise LeaderException('No active Context found for progress notification')

        progress_tracker = ProgressTracker(label)
        progress_tracker.track_start(callback=partial(self._start_progressbar, label=label))
        progress_tracker.track_step(callback=self._update_progressbar)
        progress_tracker.track_stop(callback=self._end_progressbar)
        try:
            yield
        except Exception:
            self.ctx_progressbar = None
            raise
        finally:
            progress_tracker.untrack()


class VoiceLeader(Leader):
    @property
    def attrs(self) -> dict[str, Any]:
        return {'invoke_without_command': True}

    def invoke(self, *args: Any, **kwargs: Any) -> None:
        assert self.ctx
        if self.ctx.invoked_subcommand:
            return super().invoke(*args, **kwargs)
