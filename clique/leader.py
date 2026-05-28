"""
TBD: Docstring
"""

from contextlib import contextmanager
from functools import partial
from string import Template
from typing import Any

import click
from click import progressbar

from .progress_notification import ProgressTracker


class Leader:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._message_templates: dict[str, str] = {}
        self._progress_bar_factory = progressbar

    @property
    def attrs(self) -> dict[str, Any]:
        return {}

    @property
    def ctx(self):
        return click.get_current_context(silent=True)

    @property
    def ctx_progress_bar(self):
        if hasattr(self.ctx, '__progressbar__'):
            return self.ctx.__progressbar__

    @ctx_progress_bar.setter
    def ctx_progress_bar(self, progress_bar) -> None:
        assert self.ctx
        self.ctx.__progressbar__ = progress_bar

    def invoke(self, *args, **kwargs) -> None:
        pass

    def _echo(self, *args, **kwargs) -> None:  # noqa: PLR6301
        click.secho(*args, **kwargs)

    def insert_message_templates(self, templates: dict[str, str]):
        self._message_templates.update(templates)

    def send_message(
        self, text: str | None = None, key: str | None = None, values: dict[str, str] | None = None, **kwargs: Any
    ) -> None:
        if key:
            assert not text, 'Cannot mix raw text and template key'
            if template := self._message_templates.get(key):
                text = Template(template).safe_substitute(**values) if values else template

        if not text:
            return
        self._echo(text, **kwargs)

    def _start_progress_bar(self, label: str, length: int):
        assert self.ctx_progress_bar is None, 'Cannot raise several progress bars simultaneously'
        self.ctx_progress_bar = self._progress_bar_factory(label=label, length=length)
        self.ctx_progress_bar.__enter__()  # pylint: disable=unnecessary-dunder-call

    def _update_progress_bar(self, step: int, position: int) -> None:
        assert self.ctx_progress_bar, 'No ProgressBar object found for updating'
        self.ctx_progress_bar.update(step, position)

    def _end_progress_bar(self) -> None:
        assert self.ctx_progress_bar, 'No ProgressBar object found for stopping'
        self.ctx_progress_bar.__exit__(None, None, None)
        self.ctx_progress_bar = None

    @contextmanager
    def progress_notification(self, label: str):
        assert self.ctx, 'No active Context found for progress notification'
        progress_tracker = ProgressTracker(label)
        progress_tracker.track_start(callback=partial(self._start_progress_bar, label=label))
        progress_tracker.track_step(callback=self._update_progress_bar)
        progress_tracker.track_stop(callback=self._end_progress_bar)
        try:
            yield
        except Exception as error:
            self.ctx_progress_bar = None
            raise error
        finally:
            progress_tracker.untrack()


class VoiceLeader(Leader):
    @property
    def attrs(self) -> dict[str, Any]:
        return {'invoke_without_command': True}

    def invoke(self, *args, **kwargs):
        if self.ctx.invoked_subcommand:
            return
        group = self.ctx.command
