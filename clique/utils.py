import copy
import logging
from collections.abc import Callable
from functools import partial, update_wrapper
from typing import Any, Final

from click import Command, Option, make_pass_decorator

from .core import CliqueGroup
from .exceptions import CliqueException
from .leader import Leader

_logger = logging.getLogger(__name__)


class Sentinel:
    pass


NOTHING: Final[Sentinel] = Sentinel()

pass_leader = make_pass_decorator(Leader)


def _partial(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Callable[..., Any]:
    return update_wrapper(partial(func, *args, **kwargs), func)


def set_message_templates(message_templates: dict[str, str]):
    def inner(func):
        if not isinstance(func, CliqueGroup):
            raise CliqueException('Cannot set templates keys on non CliqueGroup object')
        func.leader.insert_message_templates(message_templates)
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
        assert new_command.callback is not None
        new_command.callback = _partial(new_command.callback, **overridden_params)

    return new_command
