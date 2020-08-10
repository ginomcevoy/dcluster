from dcluster.deps import docker_dep


def configure_init_parser(init_parser):
    '''
    Configure argument parser for init subcommand.
    '''
    # default function to call
    init_parser.set_defaults(func=process_init_cli_call)


def process_init_cli_call(args):
    '''
    Process the init request issued via the command line.
    '''
    docker_dep.ensure_docker_package()
    docker_dep.ensure_docker_compose()
