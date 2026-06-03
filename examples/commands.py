# from clique.utils import clique_group
import logging
import sys
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from multiprocessing.pool import ThreadPool

import click

from clique import pass_leader
from clique.core import CliqueGroup
from clique.leader import VoiceLeader, Leader
from clique.progress_notification import progress_generator
from clique.utils import set_logger


def func_n():
    _logger.debug('### func_a info')
    for i in progress_generator(range(10), 'label'):
        print(f'Progress {i}')
        # sleep(10)


# message templated
# logger - (file?)
# progress class
# VoiceLeader - AI
# logo
# tests
# examples
# docs


_logger = logging.getLogger(__name__)


@click.group(cls=CliqueGroup, log_settings={'stream': sys.stdout, 'default_level': logging.WARNING})
@click.pass_context
# @set_logger(default_log_level=logging.INFO)  # allow set_logger in Clique?
def gr(context):
    func_n()
    _logger.info('info')
    _logger.warning('Warn')
    _logger.critical('cr')
    _logger.error('er')
    print('group', context.invoked_subcommand)


@click.group(cls=CliqueGroup, log_settings={'stream': sys.stdout, 'file_path': 'aaa'})
@click.pass_context
def gr2(context):
    func_n()
    print('group', context.invoked_subcommand)


# set logger?
# def f_2(leader, index):
#     print(index)
#     with leader.progress_notification('label'):
#         func_n()


@click.command('aaa')
@pass_leader
@click.pass_context
@click.option('-v', '--verbose', count=True, default=0)
def cmd(context, leader, verbose):
    print('aaaa', leader.ctx.invoked_subcommand, context.invoked_subcommand)
    """docstring"""
    # assert not ctx.invoked_subcommand
    # pool = ProcessPoolExecutor()
    # pool_2 = ThreadPool()
    # f = partial(f_2, leader)
    #     pool_2.map()
    # with leader.progress_notification('label'):
    #     #     # from time import sleep
    #     func_n()
    #     # sleep(10)
    # # for _ in pool.map(f, range(10)):
    # func_n()
    pass

    # with leader.progress_notification('label'):
    #     func_n()
    # func_n()
    # leader.send_message('aaaaa', bold=True)


gr2.add_command(cmd, 'new', aliases=['al'])

if __name__ == '__main__':
    # gr()
    gr2()
