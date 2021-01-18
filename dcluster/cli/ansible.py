
from dcluster.config import dansible_config
from dcluster import dansible


def configure_ansible_parser(ansible_parser):
    '''
    Configure argument parser for ansible subcommand.
    '''
    help_msg = 'Run one or more Ansible playbooks on existing cluster (list)'
    ansible_parser.add_argument('playbook', help=help_msg, nargs='+')

    help_msg = 'Name of cluster, should exist (required argument)'
    ansible_parser.add_argument('-c', '--cluster', help=help_msg)

    help_msg = 'extra-vars passed to ansible-playbook as-is'
    ansible_parser.add_argument('-e', '--extra-vars', help=help_msg, nargs='+')

    # default function to call
    ansible_parser.set_defaults(func=process_ansible_cli_call)


def process_ansible_cli_call(args):
    '''
    Process the request to execute one or more Ansible playbooks.
    '''
    if args.cluster is None:
        raise ValueError('Need to supply the cluster name!')

    inventory_file = dansible_config.default_inventory(args.cluster)

    # handle additional inventory data (variables)
    extra_vars_list = args.extra_vars
    if extra_vars_list is None:
        extra_vars_list = []

    # run requested Ansible playbooks with optional extra vars
    for playbook in args.playbook:
        dansible.run_playbook(args.cluster, playbook, inventory_file,
                              extra_vars_list)
