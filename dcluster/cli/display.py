from dcluster.actions import display as display_action


def configure_show_parser(show_parser):
    '''
    Configure argument parser for show subcommand
    '''
    show_parser.add_argument('cluster_name', help='name of the virtual cluster')

    # default function to call
    show_parser.set_defaults(func=process_show_cli_call)


def configure_list_parser(list_parser):
    '''
    Configure argument parser for list subcommand
    '''
    list_parser.set_defaults(func=process_list_cli_call)


def process_show_cli_call(args):
    '''
    Process the show request through command line
    '''
    display_action.show_cluster(args.cluster_name)


def process_list_cli_call(args):
    '''
    Process the list request through command line
    '''
    display_action.list_clusters()
