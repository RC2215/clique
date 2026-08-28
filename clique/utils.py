from collections.abc import Callable
from copy import copy
from functools import partial, update_wrapper, wraps
from typing import Any

import click
from click import Command

from .exceptions import CliqueException
from .leader import Leader

LEADER_KEY = f'{__name__}.leader'

COMMAND_ATTR_NAMES = {
    'context_settings',
    'help',
    'epilog',
    'short_help',
    'options_metavar',
    'add_help_option',
    'no_args_is_help',
    'hidden',
    'deprecated',
}


def _set_leader(ctx: click.Context, leader: Leader) -> None:
    ctx.meta[LEADER_KEY] = leader


def find_leader() -> Leader | None:
    ctx = click.get_current_context(silent=True)
    return ctx.meta.get(LEADER_KEY) if ctx else None


def pass_leader(func):
    @wraps(func)
    def new_func(*args, **kwargs):
        ctx = click.get_current_context(silent=True)
        if ctx is None or (leader := ctx.meta.get(LEADER_KEY)) is None:
            raise CliqueException('No Leader object found')
        return ctx.invoke(func, leader, *args, **kwargs)

    return new_func


def _partial(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Callable[..., Any]:
    return update_wrapper(partial(func, *args, **kwargs), func)


def clone_command(cmd: Command, name: str, overrides: dict[str, Any], **attrs: Any) -> Command:
    """
    Create a new command based on an existing one, with predefined parameter values.
    Note: Overridden parameters are removed and bound directly to the command callback.
          Consequently, any special handling associated with those parameters no longer applies.

    :param name: Name of the new command, underscores are replaced with hyphens.
    :param cmd: Base Click command instance to inherit from.
    :param overrides: Dictionary mapping parameter names to their overridden values.
    :param attrs: Additional keyword attributes overriding attributes of :class:`Command`.
    :return: A new :class:`Command` instance.
    """
    if unknown_params := (set(overrides) - {param.name for param in cmd.params}):
        raise CliqueException(f'Unknown parameters for {cmd}: {", ".join(unknown_params)}')

    if unknown_attrs := (set(attrs) - COMMAND_ATTR_NAMES):
        raise CliqueException(f'Unknown attributes for {cmd}: {", ".join(unknown_attrs)}')

    name = name.lower().replace('_', '-')
    params = [copy(param) for param in cmd.params if param.name not in overrides]
    callback = _partial(cmd.callback, **overrides) if cmd.callback is not None else None
    attrs = {name: getattr(cmd, name) for name in COMMAND_ATTR_NAMES} | attrs

    return cmd.__class__(name=name, params=params, callback=callback, **attrs)
