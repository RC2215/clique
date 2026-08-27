import logging
import sys
from collections.abc import Callable, MutableMapping, Sequence
from functools import wraps
from gettext import gettext as _
from os import PathLike
from typing import Any, Concatenate, ParamSpec, TextIO, TypeVar, cast

from click import Command, Context, Group, HelpFormatter, Option

from ._logger import set_logger
from ._typing import LogSettings
from .exceptions import CliqueException
from .leader import Leader
from .utils import _set_leader

_logger = logging.getLogger(__name__)


P = ParamSpec('P')
R = TypeVar('R')


class CliqueGroup(Group):
    """
    TBD

    :param name:
    :param commands:
    :param leader_class:
    :param message_templates:
    :param log_settings:
    :param attrs:
    """

    callback: Callable[..., Any] | None

    def __init__(
        self,
        name: str | None = None,
        commands: MutableMapping[str, Command] | Sequence[Command] | None = None,
        leader_class: type[Leader] = Leader,
        message_templates: dict[str, str] | None = None,
        log_settings: LogSettings | None = None,
        **attrs: Any,
    ) -> None:
        if not isinstance(leader_class, type) or not issubclass(leader_class, Leader):
            raise CliqueException(f'{leader_class=} must be a subclass of {Leader}')
        self._leader = leader_class(message_templates)

        self._aliases: dict[str, str] = {}
        self._commands_names: dict[str, list[str]] = {}
        self._commands_help: dict[str, str] = {}

        super().__init__(name, commands, **attrs, **self._leader.attrs)
        if log_settings is not None:
            self._set_logger(**log_settings)

    def _set_logger(
        self,
        default_level: int | None = None,
        stream: TextIO = sys.stdout,
        file_path: str | PathLike[str] | None = None,
    ) -> None:
        """
        TPD

        :param default_level:
        :param stream:
        :param file_path:
        """
        if default_level is None or self.callback is None:
            return

        def wrapper(callback: Callable[P, R]) -> Callable[Concatenate[int, P], R]:
            @wraps(callback)
            def callback_wrapper(verbose: int, *args: P.args, **kwargs: P.kwargs) -> R:
                verbosity = verbose * 10
                set_logger(default_level - verbosity, stream, file_path)
                return callback(*args, **kwargs)

            return cast(Callable[Concatenate[int, P], R], callback_wrapper)

        self.params.append(Option(['-v', '--verbose'], count=True, default=0))
        self.callback = wrapper(self.callback)

    def add_command(
        self,
        cmd: Command,
        name: str | None = None,
        help_text: str | None = None,
        aliases: list[str] | None = None,
    ) -> None:
        """
        TBD

        :param cmd:
        :param name:
        :param help_text:
        :param aliases:
        """
        name = name or cmd.name
        super().add_command(cmd, name)
        assert name is not None

        if help_text is not None:
            self._commands_help[name] = help_text

        aliases = aliases or []
        self._commands_names[name] = sorted(aliases)
        for alias in (name, *aliases):
            self._aliases[alias] = name

    def get_command(self, ctx: Context, cmd_name: str) -> Command | None:
        cmd_name = self._aliases.get(cmd_name, cmd_name)
        return super().get_command(ctx, cmd_name)

    def format_commands(self, ctx: Context, formatter: HelpFormatter) -> None:
        commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None or cmd.hidden:
                continue
            commands.append((subcommand, cmd))

        if commands:
            limit = formatter.width - 6 - max(len(cmd[0]) for cmd in commands)

            rows = []
            for subcommand, cmd in commands:
                if (cmd_help := self._commands_help.get(subcommand)) is None:
                    cmd_help = cmd.get_short_help_str(limit)
                if aliases := self._commands_names[subcommand]:
                    subcommand = f'{subcommand} ({", ".join(aliases)})'
                rows.append((subcommand, cmd_help))

            if rows:
                with formatter.section(_('Commands')):
                    formatter.write_dl(rows)

    def invoke(self, ctx: Context) -> Any:
        _set_leader(ctx, self._leader)
        super().invoke(ctx)
        self._leader.invoke()
