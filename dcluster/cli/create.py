'''
Create a cluster via the command line.
'''

import logging


from dcluster.config import main_config
from dcluster.actions import create as create_action
from dcluster.cluster import request


def configure_parser(create_parser):
    '''
    Configure argument parser for create subcommand.
    '''
    create_parser.add_argument('cluster_name', help='name of the virtual cluster')
    create_parser.add_argument('compute_count', help='number of compute nodes in cluster')

    # optional arguments
    help_msg = 'cluster flavor, see configuration file (default: %(default)s)'
    create_parser.add_argument('-f', '--flavor', default='simple',
                               help=help_msg)

    msg = 'directory where cluster files are created (default: %(default)s)'
    create_parser.add_argument('--workpath', help=msg, default=main_config.paths('work'))

    msg = 'additional directories with flavors in YAML files (can be specified multiple times)'
    create_parser.add_argument('--flavor-path', help=msg, action='append')

    msg = 'run these ansible playbooks immediately after creating the cluster (list)'
    create_parser.add_argument('--playbooks', help=msg, nargs='+')

    # default function to call
    create_parser.set_defaults(func=process_cli_call)


def process_cli_call(args):
    '''
    Process the creation request issued via the command line.
    '''
    log = logging.getLogger()
    log.debug('Got create parameters: {}'.format(args))

    # get arguments
    cluster_name = args.cluster_name
    flavor = args.flavor
    count = int(args.compute_count)
    flavor_paths = args.flavor_path  # append will create a list
    if flavor_paths is None:
        flavor_paths = []

    playbooks = args.playbooks
    if playbooks is None:
        playbooks = []

    # dispatch a creation request
    # for now, all creation requests that pass through this CLI are 'basic'
    creation_request = request.BasicCreationRequest(cluster_name, count, flavor, flavor_paths,
                                                    playbooks)
    create_action.create_basic_cluster(creation_request)
