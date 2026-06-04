import copy
from collections.abc import Callable
from functools import partial, update_wrapper
from typing import Any, Final

from click import Command, Option, make_pass_decorator

from .exceptions import CliqueException
from .leader import Leader


class Sentinel:
    pass


NOTHING: Final[Sentinel] = Sentinel()

pass_leader = make_pass_decorator(Leader)


def _partial(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Callable[..., Any]:
    return update_wrapper(partial(func, *args, **kwargs), func)


def make_sub_command(
    name: str, cmd: Command, default_map: dict[str, Any], help_text: str | None = None, force: bool = True
) -> Command:
    """
    Create a new command based on an existing one, with predefined parameter values.
    Note: The base command is deep-copied to avoid mutating the original instance.

    :param name: Name of the new command, underscores are replaced with hyphens.
    :param cmd: Base Click command instance to inherit from.
    :param default_map: Dictionary mapping parameter names to their new default values.
    :param help_text: Optional updated help text for the new command.
    :param force: If True, overridden parameters are removed and bound directly to the callback.
                  If False, default values are updated on the parameters and Options are hidden.
    :return: A new Click command instance.
    """
    if unknown_params := (set(default_map) - set(param.name for param in cmd.params)):
        raise CliqueException(f'Unknown {cmd} params passed: {", ".join(unknown_params)}')

    new_command = copy.deepcopy(cmd)
    new_command.name = name.lower().replace('_', '-')
    if help_text is not None:
        new_command.help = help_text
    overridden_params: dict[str, Any] = {}

    for param in new_command.params:
        value = default_map.get(param.name, NOTHING)
        if value is not NOTHING:
            if force:
                overridden_params[param.name] = value
            else:
                param.default = value
                if isinstance(param, Option):
                    param.hidden = True

    if overridden_params:
        assert new_command.callback is not None
        new_command.params = [param for param in new_command.params if param.name not in overridden_params]
        new_command.callback = _partial(new_command.callback, **overridden_params)

    return new_command
