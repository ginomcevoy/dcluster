from dcluster.config import main_config


def configure_ssh_parser(ssh_parser):
    '''
    Configure argument parser for ssh subcommand.
    '''
    ssh_parser.add_argument('cluster_name', help='name of the Docker cluster')
    ssh_parser.add_argument('target', help='hostname of the cluster node, can be user@hostname')

    # default function to call
    ssh_parser.set_defaults(func=process_ssh_cli_call)


def configure_scp_parser(scp_parser):
    '''
    Configure argument parser for scp subcommand.
    '''
    scp_parser.add_argument('cluster_name', help='name of the Docker cluster')
    scp_parser.add_argument('target', help='hostname of the cluster node, can be user@hostname')
    scp_parser.add_argument("files", nargs="*")

    # default function to call
    scp_parser.set_defaults(func=process_scp_cli_call)


def process_ssh_cli_call(args):
    '''
    Performs SSH to a node in the cluster.
    The node can have username@hostname, or only hostname (uses default ssh_user).
    '''
    # to avoid chain of dependencies (docker!) before dcluster init
    from dcluster.actions import ssh as ssh_action

    (cluster_name, username, hostname, _) = interpret_ssh_args(args)
    ssh_action.ssh(cluster_name, username, hostname)


def process_scp_cli_call(args):
    '''
    Copies via SSH to a node in the cluster.
    The node can have username@hostname, or only hostname (uses default ssh_user)
    Can send one or more files.
    '''
    # to avoid chain of dependencies (docker!) before dcluster init
    from dcluster.actions import ssh as ssh_action

    (cluster_name, username, hostname, target_dir) = interpret_ssh_args(args)

    # handle scp of multiple files
    files = args.files
    if not isinstance(args.files, list):
        files = [args.files, ]

    ssh_action.scp(cluster_name, username, hostname, target_dir, files)


def interpret_ssh_args(args):
    '''
    Parses the arguments received for SSH/scp.
    Takes care of username@container as a target, and the target path for scp.
    '''
    # to avoid chain of dependencies (docker!) before dcluster init
    from dcluster.actions import ssh as ssh_action

    cluster_name = args.cluster_name
    target_dir = ''

    # handle user@hostname
    if '@' in args.target:
        (username, hostname) = args.target.split('@')
    else:
        username = main_config.prefs('ssh_user')
        hostname = args.target

    # handle scp target dir
    if ':' in hostname:
        (hostname, target_dir) = hostname.split(':')

    return (cluster_name, username, hostname, target_dir)
