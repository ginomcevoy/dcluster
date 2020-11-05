'''
Main entry point for dcluster-ansible.
'''

import argparse
import logging
import sys

from dcluster.config import main_config, dansible_config
from dcluster import dansible


def process_playbook(args):
    '''
    Process the request to execute an Ansible playbook.
    '''
    inventory_file = dansible_config.default_inventory(args.cluster_name)

    # handle additional inventory data (variables)
    extra_vars_list = args.extra_vars
    if extra_vars_list is None:
        extra_vars_list = []

    # extra_vars = None
    # if args.yum:

    #     # load the '--yum <file>' as a JSON with extra variables for Ansible.
    #     # TODO reuse this for other optional arguments?
    #     extra_vars = '@%s' % args.yum

    dansible.run_playbook(args.cluster_name, args.playbook_name, inventory_file, extra_vars_list)


def configure_playbook_parser(playbook_parser):
    '''
    Adds the required and optional arguments for the 'playbook' subcommand.

    TODO: reuse some/all optional arguments for 'dcluster create' command?
    '''
    playbook_parser.add_argument('cluster_name', help='name of the Docker cluster')
    playbook_parser.add_argument('playbook_name', help='playbook identifier (TODO: show list?)')
    # playbook_parser.add_argument('--yum', default=None, help='JSON file with yum repositories')

    msg = 'extra-vars passed to ansible-playbook as-is'
    playbook_parser.add_argument('-e', '--extra-vars', help=msg, nargs='+')

    playbook_parser.set_defaults(func=process_playbook)


def processRequest():
    '''
    Handle the program execution using argparse.

    For now, only the 'playbook' subcommand is supported.
    '''
    # top level parser
    desc = 'dcluster-ansible: run/manage Ansible playbooks on dcluster containers'
    parser = argparse.ArgumentParser(prog='dcluster-ansible', description=desc)
    subparsers = parser.add_subparsers(help='Run dcluster <command> for additional help')

    # below we create subparsers for the subcommands
    playbook_parser = subparsers.add_parser('playbook', help='run an Ansible playbook')
    configure_playbook_parser(playbook_parser)

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
