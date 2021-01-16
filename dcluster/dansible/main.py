'''
Main entry point for dcluster-ansible.
'''

import argparse
import logging
import sys

from dcluster.config import main_config, dansible_config
from dcluster import dansible


def process_playbooks(args):
    '''
    Process the request to execute one or more Ansible playbooks.
    '''
    inventory_file = dansible_config.default_inventory(args.cluster_name)

    # handle additional inventory data (variables)
    extra_vars_list = args.extra_vars
    if extra_vars_list is None:
        extra_vars_list = []

    # run requested Ansible playbooks with optional extra vars
    for playbook in args.playbooks:
        dansible.run_playbook(args.cluster_name, playbook, inventory_file,
                              extra_vars_list)


def configure_parser(parser):
    '''
    Adds the required and optional arguments the parser.
    '''
    parser.add_argument('cluster_name', help='name of the Docker cluster')
    parser.add_argument('playbooks', help='one or more playbooks to execute', nargs='+')

    msg = 'extra-vars passed to ansible-playbook as-is'
    parser.add_argument('-e', '--extra-vars', help=msg, nargs='+')

    parser.set_defaults(func=process_playbooks)


def processRequest():
    '''
    Handle the program execution using argparse.
    Only one parser that deals with the execution of playbooks on a cluster.
    '''
    # top level parser
    desc = 'dcluster-ansible: run/manage Ansible playbooks on dcluster containers'
    parser = argparse.ArgumentParser(prog='dcluster-ansible', description=desc)
    configure_parser(parser)

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
