import argparse
import logging
import sys

from dcluster.config import main_config
from dcluster import dansible


def process_playbook(args):
    inventory_file = main_config.default_inventory(args.cluster_name)
    dansible.run_playbook(args.cluster_name, args.playbook_name, inventory_file)


def configure_playbook_parser(playbook_parser):
    playbook_parser.add_argument('cluster_name', help='name of the Docker cluster')
    playbook_parser.add_argument('playbook_name', help='playbook identifier (TODO: show list?)')

    playbook_parser.set_defaults(func=process_playbook)


def processRequest():

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


if __name__ == "__main__":

    log_level_str = main_config.prefs('log_level')
    log_level = getattr(logging, log_level_str)
    logging.basicConfig(format='%(asctime)s - %(levelname)6s | %(message)s',
                        level=log_level, datefmt='%d-%b-%y %H:%M:%S')
    processRequest()
