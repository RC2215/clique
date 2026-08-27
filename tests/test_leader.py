import click
import pytest

from clique import CliqueException, CliqueGroup, Leader


def test_invalid_leader_class():
    class Administrator:
        pass

    for invalid_leader in (Administrator, Leader()):
        with pytest.raises(CliqueException, match=f'must be a subclass of {Leader}'):

            @click.group(cls=CliqueGroup, leader_class=invalid_leader)
            def group():
                pass
