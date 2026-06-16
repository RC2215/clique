from collections.abc import Callable
from copy import copy
from functools import partial, update_wrapper
from typing import Any

from click import Command, Option, Parameter, make_pass_decorator

from .exceptions import CliqueException
from .leader import Leader

pass_leader = make_pass_decorator(Leader)


def _partial(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Callable[..., Any]:
    return update_wrapper(partial(func, *args, **kwargs), func)


def clone_command(cmd: Command, name: str, default_map: dict[str, Any], force: bool = True, **kwargs: Any) -> Command:
    """
    Create a new command based on an existing one, with predefined parameter values.

    :param name: Name of the new command, underscores are replaced with hyphens.
    :param cmd: Base Click command instance to inherit from.
    :param default_map: Dictionary mapping parameter names to their new default values.
    :param force: If True, overridden parameters are removed and bound directly to the callback.
                  If False, default values are updated on the parameters and Options are hidden.
    :param kwargs: Other arguments passed to :class:`Command`.
    :return: A new :class:`Command` instance.
    """
    if unknown_params := (set(default_map) - set(param.name for param in cmd.params)):
        raise CliqueException(f'Unknown {cmd} params passed to default map: {", ".join(unknown_params)}')

    params: list[Parameter] = [copy(param) for param in cmd.params if param.name not in default_map]

    cmd_kwargs = {
        'context_settings': cmd.context_settings,
        'help': cmd.help,
        'epilog': cmd.epilog,
        'short_help': cmd.short_help,
        'options_metavar': cmd.options_metavar,
        'add_help_option': cmd.add_help_option,
        'no_args_is_help': cmd.no_args_is_help,
        'hidden': cmd.hidden,
        'deprecated': cmd.deprecated,
        **kwargs,
    }

    if force:
        cmd_kwargs['callback'] = _partial(cmd.callback, **default_map) if cmd.callback is not None else None
    else:
        for param in cmd.params:
            if param.name in default_map:
                param = copy(param)
                param.default = default_map.get(param.name)
                if isinstance(param, Option):
                    param.hidden = True
                params.append(param)

    command = cmd.__class__(name=name.lower().replace('_', '-'), params=params, **cmd_kwargs)
    return command
