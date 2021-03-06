'''
Main entry point of dcluster.
'''

import argparse
import logging
import sys

# from six.moves import input

from dcluster.config import main_config

from dcluster.cli import create as create_cli
from dcluster.cli import display as display_cli
from dcluster.cli import manage as manage_cli
from dcluster.cli import ssh as ssh_cli
from dcluster.cli import init as init_cli
from dcluster.cli import ansible as ansible_cli


def processRequest():
    '''
    Handle 'dcluster' requests using argparse and subparsers for each subcommand.
    '''

    # top level parser
    desc = 'dcluster: deploy clusters of Docker containers'
    parser = argparse.ArgumentParser(prog='dcluster', description=desc)
    subparsers = parser.add_subparsers(help='Run dcluster <command> for additional help')

    # below we create subparsers for the subcommands
    create_parser = subparsers.add_parser('create', help='create a cluster')
    create_cli.configure_parser(create_parser)

    show_parser = subparsers.add_parser('show', help='show details of a cluster')
    display_cli.configure_show_parser(show_parser)

    ssh_parser = subparsers.add_parser('ssh', help='SSH into a container of a cluster')
    ssh_cli.configure_ssh_parser(ssh_parser)

    scp_parser = subparsers.add_parser('scp', help='Copy via SSH to a container of a cluster')
    ssh_cli.configure_scp_parser(scp_parser)

    stop_parser = subparsers.add_parser('stop', help='stop a running cluster')
    manage_cli.configure_stop_parser(stop_parser)

    start_parser = subparsers.add_parser('start', help='start a stopped cluster')
    manage_cli.configure_start_parser(start_parser)

    rm_parser = subparsers.add_parser('rm', help='remove a running or stopped cluster')
    manage_cli.configure_rm_parser(rm_parser)

    list_parser = subparsers.add_parser('list', help='list current clusters')
    display_cli.configure_list_parser(list_parser)

    ansible_parser = subparsers.add_parser('ansible', help='run ansible playbooks on a cluster')
    ansible_cli.configure_ansible_parser(ansible_parser)

    init_parser = subparsers.add_parser('init', help='setup dcluster dependencies')
    init_cli.configure_init_parser(init_parser)

    # show help if no subcommand is given
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # activate parsing and sub-command function call
    # note: we expect args.func(args) to succeed, since we are making sure we have subcommands
    args = parser.parse_args()
    args.func(args)


def main():
    log_level_str = main_config.prefs('log_level')
    log_level = getattr(logging, log_level_str)
    logging.basicConfig(format='%(asctime)s - %(levelname)6s | %(message)s',
                        level=log_level, datefmt='%d-%b-%y %H:%M:%S')
    processRequest()


if __name__ == "__main__":
    main()
