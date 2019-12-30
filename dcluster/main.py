'''
Main entry point of dcluster.
'''

import argparse
import logging
import os
import sys

# from six.moves import input

from . import cluster


def process_creation(args):

    log = logging.getLogger()
    log.debug('Got create parameters %s %s %s' % (args.cluster_name, args.compute_count,
                                                  args.basepath))

    # create the request and call factory method
    cluster_specs = cluster.ClusterRequestSimple(args.cluster_name, int(args.compute_count))
    cluster.create(cluster_specs, args.basepath)


def configure_create_parser(create_parser):
    create_parser.add_argument('cluster_name', help='name of the Docker cluster')
    create_parser.add_argument('compute_count', help='number of compute nodes in cluster')

    msg = 'directory where cluster files are created (set to $PWD by script)'
    create_parser.add_argument('--basepath', help=msg)

    # default function to call
    create_parser.set_defaults(func=process_creation)


def process_show(args):

    log = logging.getLogger()
    log.debug('Got show parameter %s' % args.cluster_name)

    docker_cluster = cluster.DockerCluster.from_docker(args.cluster_name)
    formatter = cluster.DockerClusterFormatterText()
    output = docker_cluster.format(formatter)
    print(output)


def configure_show_parser(show_parser):
    show_parser.add_argument('cluster_name', help='name of the Docker cluster')

    # ignored
    show_parser.add_argument('--basepath')

    # default function to call
    show_parser.set_defaults(func=process_show)


def process_stop(args):

    docker_cluster = cluster.DockerCluster.from_docker(args.cluster_name)
    docker_cluster.stop()


def configure_stop_parser(stop_parser):
    stop_parser.add_argument('cluster_name', help='name of the Docker cluster')

    # ignored
    stop_parser.add_argument('--basepath')

    # default function to call
    stop_parser.set_defaults(func=process_stop)


def process_ssh(args):

    docker_cluster = cluster.DockerCluster.from_docker(args.cluster_name)
    docker_cluster.ssh_to_node(args.hostname)


def configure_ssh_parser(ssh_parser):
    ssh_parser.add_argument('cluster_name', help='name of the Docker cluster')
    ssh_parser.add_argument('hostname', help='hostname of the cluster node')

    # ignored
    ssh_parser.add_argument('--basepath')

    # default function to call
    ssh_parser.set_defaults(func=process_ssh)


def process_list(args):

    networks = cluster.DockerCluster.list_all()
    print('\n'.join(networks))


def configure_list_parser(list_parser):
    # ignored
    list_parser.add_argument('--basepath')

    list_parser.set_defaults(func=process_list)


def process_rm(args):

    docker_cluster = cluster.DockerCluster.from_docker(args.cluster_name)
    docker_cluster.remove()


def configure_rm_parser(rm_parser):
    rm_parser.add_argument('cluster_name', help='name of the Docker cluster')

    # ignored
    rm_parser.add_argument('--basepath')

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
    # assume 'basepath <basepath>' is always passed (by script)
    if len(sys.argv) == 3:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # activate parsing and sub-command function call
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    log_level = logging.DEBUG
    logging.basicConfig(format='%(asctime)s - %(levelname)6s | %(message)s',
                        level=log_level, datefmt='%d-%b-%y %H:%M:%S')
    processRequest()
