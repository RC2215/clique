import copy
import logging
from collections.abc import Callable
from functools import partial, update_wrapper, wraps
from os import PathLike
from typing import Any, Final

from click import Command, Option, make_pass_decorator

from .core import CliqueGroup
from .exceptions import CliqueException
from .leader import Leader


class Sentinel:
    pass


NOTHING: Final[Sentinel] = Sentinel()

pass_leader = make_pass_decorator(Leader)


def _partial(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Callable[..., Any]:
    return update_wrapper(partial(func, *args, **kwargs), func)


def _set_group_attr(attr_name, attr_value):
    def inner(func):
        if not isinstance(func, CliqueGroup):
            raise CliqueException('Operation not supported on non CliqueGroup object')
        setattr(func, attr_name, attr_value)
        return func

    return inner


def set_logger(default_log_level: int = logging.INFO, file_path: str | PathLike[str] | None = None) -> None:
    pass


# set_message_template - a meta key? pass_meta_key
set_message_templates = partial(_set_group_attr, 'message_templates')
# set_logger = partial(_set_group_attr, 'default_log_level')  # ? only boolean? no, with option to log_level!


def make_sub_command(name: str, cmd: Command, default_map: dict[str, Any], force: bool = True) -> Command:
    """
    TBD: Docstring
    """
    new_command = copy.deepcopy(cmd)
    new_command.name = name.lower().replace('_', '-')
    overridden_params: dict[str, Any] = {}

    for param in new_command.params.copy():
        value = default_map.get(param.name, NOTHING)
        if value is not NOTHING:
            default_map.pop(param.name)
            if force:
                new_command.params.remove(param)
                overridden_params[param.name] = value
            else:
                param.default = value
                if isinstance(param, Option):
                    param.hidden = True

    if default_map:
        raise CliqueException(f'Unknown {cmd.name} params: {list(default_map.keys())}')

    if overridden_params:
        assert new_command.callback is not None
        new_command.callback = _partial(new_command.callback, **overridden_params)

    return new_command
