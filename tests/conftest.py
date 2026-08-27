import click
import pytest
from click.testing import CliRunner

from clique import CliqueGroup


@pytest.fixture(scope='function')
def runner():
    return CliRunner()


@pytest.fixture(scope='function')
def group():
    @click.group(cls=CliqueGroup)
    def group():
        pass

    return group
