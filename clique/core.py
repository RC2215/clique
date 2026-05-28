import logging
import sys
from collections.abc import MutableMapping, Sequence
from functools import wraps
from gettext import gettext as _
from typing import Any, Type

from click import Command, Context, Group, HelpFormatter, Option

from .exceptions import CliqueException
from .leader import Leader
from .logger import ColoredStreamFormatter

_logger = logging.getLogger(__name__)


class CliqueGroup(Group):
    def __init__(
        self,
        name: str | None = None,
        commands: MutableMapping[str, Command] | Sequence[Command] | None = None,
        leader_class: Type[Leader] = Leader,
        default_log_level: int | None = None,
        **attrs: Any,
    ):
        if not isinstance(leader_class, type) or not issubclass(leader_class, Leader):
            raise CliqueException(f'{leader_class=} must be a subclass of {Leader}')
        self._leader = leader_class()
        self._default_log_level = default_log_level

        self._aliases: dict[str, str] = {}
        self._commands_names: dict[str, list[str]] = {}
        self._commands_help: dict[str, str] = {}

        super().__init__(name, commands, **attrs, **self._leader.attrs)

    def _set_logger(self) -> None:
        if self._default_log_level is None:
            return

        def wrapper(callback):
            @wraps(callback)
            def callback_wrapper(verbose, *args, **kwargs):
                verbosity = verbose * 10
                log_level = self._default_log_level - verbosity
                logger = logging.getLogger()
                logger.setLevel(log_level)

                handler = logging.StreamHandler(sys.stdout)
                handler.setLevel(log_level)
                handler.setFormatter(ColoredStreamFormatter())
                logger.addHandler(handler)
                return callback(*args, **kwargs)

            return callback_wrapper

        self.params.append(Option(['-v', '--verbose'], count=True, default=0))
        self.callback = wrapper(self.callback)

    def make_context(
        self, info_name: str | None, args: list[str], parent: Context | None = None, **extra: Any
    ) -> Context:
        self._set_logger()
        return super().make_context(info_name, args, parent, **extra)

    def add_command(
        self,
        cmd: Command,
        name: str | None = None,
        help_text: str | None = None,
        aliases: list | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        name = name or cmd.name
        super().add_command(cmd, name)
        assert name is not None

        if help_text:
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
                subcommand = f'{subcommand} ({", ".join(self._commands_names[subcommand])})'
                cmd_help = self._commands_help.get(subcommand) or cmd.get_short_help_str(limit)
                rows.append((subcommand, cmd_help))

            if rows:
                with formatter.section(_('Commands')):
                    formatter.write_dl(rows)

    def invoke(self, ctx: Context) -> Any:
        ctx.obj = self._leader
        super().invoke(ctx)
        self._leader.invoke()  # Rename?
