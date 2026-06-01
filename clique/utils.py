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


def make_sub_command(name: str, cmd: Command, default_map: dict[str, Any], force: bool = True) -> Command:
    """
    TBD: Docstring
    """
    new_command = copy.deepcopy(cmd)
    new_command.name = name.lower().replace('_', '-')
    overridden_params: dict[str, Any] = {}

    for param in new_command.params:
        value = default_map.pop(param.name, NOTHING)
        if value is not NOTHING:
            if force:
                overridden_params[param.name] = value
            else:
                param.default = value
                if isinstance(param, Option):
                    param.hidden = True

    if default_map:
        raise CliqueException(f'Unknown {cmd.name} params: {list(default_map.keys())}')

    if overridden_params:
        assert new_command.callback is not None
        new_command.params = [param for param in new_command.params if param.name not in overridden_params]
        new_command.callback = _partial(new_command.callback, **overridden_params)

    return new_command
