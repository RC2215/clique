import copy
import logging
from functools import partial, update_wrapper, wraps
from typing import Any, Callable, Final

from click import Command, Option, get_current_context

from .core import CliqueGroup
from .exceptions import CliqueException
from .leader import Leader

_logger = logging.getLogger(__name__)

_AnyCallable = Callable[..., Any]
_Group = Callable[[_AnyCallable], CliqueGroup]


class Sentinel:
    pass


NOTHING: Final[Sentinel] = Sentinel()


def _partial(func: Callable, *args, **kwargs):
    return update_wrapper(partial(func, *args, **kwargs), func)


def find_leader() -> Leader | None:
    """
    TBD: Docstring
    """
    ctx = get_current_context(silent=True)

    while ctx is not None:
        cmd = ctx.command
        if isinstance(cmd, CliqueGroup):
            return cmd.leader

        ctx = ctx.parent

    return None


def pass_leader(func):
    """
    TBD: Docstring
    """
    @wraps(func)
    def new_func(*args, **kwargs):
        leader = find_leader()
        assert leader, 'No Leader object found'
        return func(leader, *args, **kwargs)

    return new_func


def set_message_templates(templates: dict[str, str]):
    """
    TBD: Docstring
    """
    def inner(func):
        if not isinstance(func, CliqueGroup):
            raise CliqueException('Cannot set templates keys on non CliqueGroup object')
        func.leader.insert_message_templates(templates)
        return func

    return inner


def make_sub_command(name: str, cmd: Command, default_map: dict[str, Any], force: bool = True) -> Command:
    """
    TBD: Docstring
    """
    new_command = copy.deepcopy(cmd)
    new_command.name = name.lower().replace('_', '-')
    overridden_params: dict[str, Any] = {}

    for param in new_command.params:
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
        new_command.callback = _partial(new_command.callback, **overridden_params)

    return new_command
