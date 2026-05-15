"""
TBD: Docstring
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from functools import partial
from string import Template
from typing import Any

import click
from click import progressbar

from clique.progress_notification import ProgressTracker


class Leader(ABC):
    def __init__(self):
        self._messages_templates: dict[str, str] = {}

    @staticmethod
    def get_group_attrs() -> dict[str, Any]:
        return {}

    @abstractmethod
    def invoke_group(self):
        pass

    @abstractmethod
    def _echo(self, *args, **kwargs) -> None:
        pass

    @property
    def ctx(self):
        return click.get_current_context(silent=True)

    def send_message(self, text: str = None, key: str = None, values: dict[str, str] = None, **kwargs: Any) -> None:
        if key:
            assert not text, 'Cannot mix raw text and template key'
            if template := self._messages_templates.get(key):
                text = Template(template).safe_substitute(**values)

        if not text:
            return
        self._echo(text, **kwargs)

    def insert_message_templates(self, templates: dict[str, str]):
        self._messages_templates.update(templates)

    @property
    def ctx_progress_bar(self):
        if hasattr(self.ctx, '__progressbar__'):
            return self.ctx.__progressbar__

    @ctx_progress_bar.setter
    def ctx_progress_bar(self, progressbar):
        assert self.ctx
        self.ctx.__progressbar__ = progressbar

    def _start_progress_bar(self, label: str, length: int):
        assert self.ctx_progress_bar is None, 'Cannot raise several progress bars simultaneously'
        self.ctx_progress_bar = progressbar(label=label, length=length)
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


class CliLeader(Leader):
    def invoke_group(self):
        pass

    def _echo(self, *args, **kwargs):
        click.secho(*args, **kwargs)


class VoiceLeader(Leader):
    @staticmethod
    def get_group_attrs() -> dict[str, Any]:
        return {'invoke_without_command': True}

    def invoke_group(self):
        # invoke - generate help...
        pass

    def _echo(self, *args, **kwargs):
        click.echo(*args, **kwargs)
