#!/usr/bin/env python

'''
Main entry point of dcluster.
'''

import argparse
import logging
import sys

# from six.moves import input

from dcluster import config

from dcluster.actions import create as create_action
from dcluster.actions import display as display_action
from dcluster.actions import manage as manage_action


def process_creation(args):

    log = logging.getLogger()
    log.debug('Got create parameters %s %s %s %s' % (args.cluster_name, args.compute_count,
                                                     args.flavor, args.workpath))

    create_action.create_cluster(args)

    # display.show_cluster(cluster)


def configure_create_parser(create_parser):
    create_parser.add_argument('cluster_name', help='name of the Docker cluster')
    create_parser.add_argument('compute_count', help='number of compute nodes in cluster')

    # optional arguments
    help_msg = 'cluster flavor, see configuration file (default: %(default)s)'
    create_parser.add_argument('-f', '--flavor', default='simple',
                               help=help_msg)

    msg = 'directory where cluster files are created (default: %(default)s)'
    create_parser.add_argument('--workpath', help=msg, default=config.paths('work'))

    # default function to call
    create_parser.set_defaults(func=process_creation)


def process_show(args):

    display_action.show_cluster(args.cluster_name)


def configure_show_parser(show_parser):
    show_parser.add_argument('cluster_name', help='name of the Docker cluster')

    # default function to call
    show_parser.set_defaults(func=process_show)


def process_stop(args):
    manage_action.stop_cluster(args.cluster_name)


def configure_stop_parser(stop_parser):
    stop_parser.add_argument('cluster_name', help='name of the Docker cluster')

    # default function to call
    stop_parser.set_defaults(func=process_stop)


def process_ssh(args):
    manage_action.ssh(args)


def configure_ssh_parser(ssh_parser):
    ssh_parser.add_argument('cluster_name', help='name of the Docker cluster')
    ssh_parser.add_argument('target', help='hostname of the cluster node, can be user@hostname')

    # default function to call
    ssh_parser.set_defaults(func=process_ssh)


def process_list(args):
    display_action.list_clusters()


def configure_list_parser(list_parser):
    list_parser.set_defaults(func=process_list)


def process_rm(args):
    manage_action.remove_cluster(args.cluster_name)


def configure_rm_parser(rm_parser):
    rm_parser.add_argument('cluster_name', help='name of the Docker cluster')

    # default function to call
    rm_parser.set_defaults(func=process_rm)


def processRequest():

    # top level parser
    desc = 'clustertest: deploy clusters of Docker containers'
    parser = argparse.ArgumentParser(prog='clustertest', description=desc)
    subparsers = parser.add_subparsers(help='Run clustertest <command> for additional help')

    # below we create subparsers for the subcommands
    create_parser = subparsers.add_parser('create', help='create a cluster')
    configure_create_parser(create_parser)

    show_parser = subparsers.add_parser('show', help='show details of a cluster')
    configure_show_parser(show_parser)

    ssh_parser = subparsers.add_parser('ssh', help='connect to a container of a cluster')
    configure_ssh_parser(ssh_parser)

    stop_parser = subparsers.add_parser('stop', help='stop a running cluster')
    configure_stop_parser(stop_parser)

    rm_parser = subparsers.add_parser('rm', help='remove a running or stopped cluster')
    configure_rm_parser(rm_parser)

    list_parser = subparsers.add_parser('list', help='list current clusters')
    configure_list_parser(list_parser)

    # show help if no subcommand is given
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # activate parsing and sub-command function call
    # note: we expect args.func(args) to succeed, since we are making sure we have subcommands
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":

    log_level_str = config.prefs('log_level')
    log_level = getattr(logging, log_level_str)
    logging.basicConfig(format='%(asctime)s - %(levelname)6s | %(message)s',
                        level=log_level, datefmt='%d-%b-%y %H:%M:%S')
    processRequest()
