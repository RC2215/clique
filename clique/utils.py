from copy import copy
from collections.abc import Callable
from functools import partial, update_wrapper
from typing import Any, Final

from click import Command, Option, make_pass_decorator, Parameter

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

    # the params should be deep-copied?
    for param in new_command.params:
        value = default_map.get(param.name, NOTHING)
        if value is not NOTHING:
            if force:
                overridden_params[param.name] = value
            else:
                param.default = value  # only default_map?
                if isinstance(param, Option):
                    param.hidden = True

    if overridden_params:
        assert new_command.callback is not None
        new_command.params = [param for param in new_command.params if param.name not in overridden_params]
        new_command.callback = _partial(new_command.callback, **overridden_params)

    # new_command = cmd.__class__()
    # cmd.clone(...)

    return new_command


def clone_command(
        cmd: Command, name: str, default_map: dict[str, Any] | None = None, force: bool = True, **kwargs: Any
) -> Command:
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
        raise CliqueException(f'Unknown {cmd} params passed: {", ".join(unknown_params)}')

    params: list[Parameter] = [copy(param) for param in cmd.params if param.name not in default_map]
    overridden_params: dict[str, Any] = {}

    if not force:
        pass
    elif cmd.callback is not None:
        callback = _partial(cmd.callback, **overridden_params)


    if not force:
        for param in params:
            value = default_map.get(param.name, NOTHING)
            if value is not NOTHING:
                params.append(param)
                param.default = value
                if isinstance(param, Option):  # not hidden!
                    param.hidden = True


    for param in cmd.params:
        param = copy(param)
        value = default_map.get(param.name, NOTHING)
        if value is not NOTHING:
            if force:
                overridden_params[param.name] = value
            else:
                params.append(param)
                param.default = value
                if isinstance(param, Option):
                    param.hidden = True
        else:
            params.append(param)
        # a list of params during iteration?

        # [param for param in new_command.params if param.name not in overridden_params]

    base_cmd_kwargs = {'context_class': cmd.context_settings,
                       'allow_extra_args': cmd.allow_extra_args,
                       'allow_interspersed_args': cmd.allow_interspersed_args,
                       'ignore_unknown_options': cmd.ignore_unknown_options,
                       'context_settings': cmd.context_settings,
                       'help': cmd.help,
                       'epilog': cmd.epilog,
                       'short_help': cmd.short_help,
                       'options_metavar': cmd.options_metavar,
                       'add_help_option': cmd.add_help_option,
                       'no_args_is_help': cmd.no_args_is_help,
                       'hidden': cmd.hidden,
                       'deprecated': cmd.deprecated}

    #         params: list[Parameter] | None = None,
    callback = _partial(cmd.callback, **overridden_params) if cmd.callback is not None else None
    command = cmd.__class__(name=name.lower().replace('_', '-'), callback=callback, **base_cmd_kwargs, **kwargs)
    return command

    #     new_command.params = [param for param in new_command.params if param.name not in overridden_params]
