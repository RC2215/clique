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
    An exclusive group.

    This class extends the Click's :class:`Group` functionality.

    :param name: Name of the group command.
    :param commands: Dictionary or list of :class:`Command` objects.
    :param leader_class: :class:`Leader` class name that manages this group.
    :param message_templates: Dictionary mapping a string key to a string template, passing to the :class:`Leader`.
    :param log_settings: Dictionary for setting a logger. Keys: default_level (Required), stream, file_path.
    :param attrs: Additional keyword attributes overriding attributes of :class:`Group`.
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
        if isinstance(commands, Sequence) and len(self.commands) < len(commands):
            raise CliqueException('Conflicting names detected in the provided commands')

        if log_settings is not None:
            self._set_logger(**log_settings)

    def _set_logger(
        self,
        default_level: int | None = None,
        stream: TextIO = sys.stdout,
        file_path: str | PathLike[str] | None = None,
    ) -> None:
        if default_level is None or self.callback is None:
            raise CliqueException('Missing default level or group callback for logger setting')

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
        Register a :class:`Command` with the group.

        :param cmd: Command instance to register with the group.
        :param name: Overrides the default command's name.
        :param help_text: Overrides the default command's help text.
        :param aliases: Alternative names that can be used to invoke the command.
        """
        name = name or cmd.name
        aliases = aliases or []
        for cmd_name in (name, *aliases):
            if cmd_name in self.commands or cmd_name in self._aliases:
                raise CliqueException(f'A command named {cmd_name!r} already exists')

        super().add_command(cmd, name)
        assert name is not None

        if help_text is not None:
            self._commands_help[name] = help_text

        self._aliases.update({alias: name for alias in aliases})
        self._commands_names[name] = sorted(aliases)

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
                if aliases := self._commands_names.get(subcommand):
                    subcommand = f'{subcommand} ({", ".join(aliases)})'
                rows.append((subcommand, cmd_help))

            if rows:
                with formatter.section(_('Commands')):
                    formatter.write_dl(rows)

    def invoke(self, ctx: Context) -> Any:
        _set_leader(ctx, self._leader)
        result = super().invoke(ctx)
        self._leader.invoke()
        return result
