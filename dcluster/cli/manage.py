from dcluster.actions import manage as manage_action


def configure_stop_parser(stop_parser):
    '''
    Configure argument parser for stop subcommand
    '''
    stop_parser.add_argument('cluster_name', help='name of the virtual cluster')

    # default function to call
    stop_parser.set_defaults(func=process_stop_cli_call)


def configure_rm_parser(rm_parser):
    '''
    Configure argument parser for rm subcommand
    '''
    rm_parser.add_argument('cluster_name', help='name of the Docker cluster')

    # default function to call
    rm_parser.set_defaults(func=process_rm_cli_call)


def process_stop_cli_call(args):
    '''
    Process the stop request through command line
    '''
    manage_action.stop_cluster(args.cluster_name)


def process_rm_cli_call(args):
    '''
    Process the remove request through command line
    '''
    manage_action.remove_cluster(args.cluster_name)
