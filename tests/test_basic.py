import click
import pytest

from clique import CliqueException, CliqueGroup


def test_group_commands(runner):
    @click.command()
    def defer():
        """
        Reschedule important things for a later time
        """
        raise NotImplementedError()

    group = CliqueGroup(commands={'cancel': defer})

    result = runner.invoke(group, ['--help'])
    assert result.exit_code == 0
    assert 'defer' not in result.output
    assert 'cancel' in result.output
    assert 'Reschedule important things for a later time' in result.output

    result = runner.invoke(group, ['defer'])
    assert result.exit_code == 2
    assert "No such command 'defer'." in result.output

    result = runner.invoke(group, ['cancel'])
    assert result.exit_code == 1
    assert isinstance(result.exception, NotImplementedError)


def test_add_command(runner):
    failure_name, success_name, non_existent_name = 'idle', 'do', 'complete'

    @click.command(name=failure_name)
    def fail():
        pass

    @click.command(name=non_existent_name)
    def succeed():
        pass

    group = CliqueGroup(commands=[fail])
    with pytest.raises(CliqueException, match=f'A command named {failure_name!r} already exists'):
        group.add_command(fail)
    group.add_command(fail, name='stop')
    group.add_command(succeed, name=success_name, help_text='Just do')

    result = runner.invoke(group, ['--help'])
    assert 'Just do\n' in result.output

    result = runner.invoke(group, [success_name])
    assert result.exit_code == 0

    result = runner.invoke(group, [non_existent_name])
    assert result.exit_code == 2


def test_command_aliases(runner, group):
    @click.command()
    def status():
        """
        Report the project status
        """
        click.echo('Still working on it...')

    group.add_command(status, aliases=['stat', 'st'], help_text='')
    with pytest.raises(CliqueException, match=f'A command named {"status"!r} already exists'):
        group.add_command(status, name='poll', aliases=['status'])
    with pytest.raises(CliqueException, match=f'A command named {"st"!r} already exists'):
        group.add_command(status, name='st')

    for name in ('status', 'stat', 'st'):
        result = runner.invoke(group, [name])
        assert result.exit_code == 0
        assert result.output == 'Still working on it...\n'

    result = runner.invoke(group, ['--help'])
    assert result.exit_code == 0
    assert 'status (st, stat)\n' in result.output
    assert 'Report the project status' not in result.output
