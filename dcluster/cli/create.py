'''
Create a cluster via the command line.
'''

import logging


from dcluster import config

from dcluster.actions import create as create_action
from dcluster.cluster import request


def configure_parser(create_parser):
    '''
    Configure argument parser for create subcommand
    '''

    create_parser.add_argument('cluster_name', help='name of the virtual cluster')
    create_parser.add_argument('compute_count', help='number of compute nodes in cluster')

    # optional arguments
    help_msg = 'cluster flavor, see configuration file (default: %(default)s)'
    create_parser.add_argument('-f', '--flavor', default='simple',
                               help=help_msg)

    msg = 'directory where cluster files are created (default: %(default)s)'
    create_parser.add_argument('--workpath', help=msg, default=config.paths('work'))

    # default function to call
    create_parser.set_defaults(func=process_cli_call)


def process_cli_call(args):
    '''
    Process the creation request through command line
    '''
    log = logging.getLogger()
    log.debug('Got create parameters %s %s %s %s' % (args.cluster_name, args.compute_count,
                                                     args.flavor, args.workpath))

    # get arguments
    cluster_name = args.cluster_name
    flavor = args.flavor
    count = int(args.compute_count)

    # dispatch a creation request
    # for now, all creation requests that pass through this CLI are 'simple'
    creation_request = request.SimpleCreationRequest(cluster_name, count, flavor)
    create_action.create_simple_cluster(creation_request)
