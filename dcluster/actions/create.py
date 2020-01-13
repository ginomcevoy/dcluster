from dcluster import config, cluster, dansible, networking, plan

from dcluster.actions import display

from . import get_workpath


def interpret_args(args):
    cluster_name = args.cluster_name
    flavor = args.flavor
    count = int(args.compute_count)
    by_flavor = {
        'simple': plan.SimpleCreationRequest(cluster_name, count, flavor),
        'slurm': plan.SimpleCreationRequest(cluster_name, count, flavor)
    }
    return by_flavor[flavor]


def create_cluster(args):
    '''
    Creates a new cluster based on a creation request, it should at least have the flavor.
    '''

    creation_request = interpret_args(args)
    workpath = get_workpath(args)
    create_by_flavor = {
        'simple': create_simple_cluster,
        'slurm': create_simple_cluster
    }
    return create_by_flavor[creation_request.flavor](creation_request, workpath)


def create_simple_cluster(creation_request, workpath):
    '''
    Creates a new simple cluster, the request should have:
    - name
    - compute_count
    - flavor (should be 'simple' for now)
    '''
    # go ahead and create the network using Docker
    cluster_network = networking.create(creation_request.name)

    # develop the cluster plan given request + config
    cluster_config = config.for_cluster(creation_request.flavor)
    cluster_plan = plan.create_plan(creation_request, cluster_config, cluster_network)

    # get the blueprints with plans for all nodes
    cluster_blueprints = cluster_plan.create_blueprints()

    # deploy the cluster
    renderer = cluster.get_renderer(creation_request)
    composer_workpath = config.composer_workpath(creation_request.name)
    deployer = cluster.DockerComposeDeployer(composer_workpath)

    cluster_blueprints.deploy(renderer, deployer)

    # create the Ansible inventory now, too hard later
    cluster_name = creation_request.name
    inventory_workpath = config.inventory_workpath(cluster_name)
    (_, inventory_file) = dansible.create_inventory(cluster_blueprints.as_dict(),
                                                    inventory_workpath)

    # test
    dansible.run_playbook(cluster_name, 'hello', inventory_file)

    # show newly created
    live_cluster = display.show_cluster(creation_request.name)

    if config.prefs('inject_ssh_public_key_to_root'):
        # inject SSH public key to all containers for password-less SSH

        # public_key_with_shell_vars = config.paths('ssh_public_key')
        # public_key_path = fs_util.evaluate_shell_path(public_key_with_shell_vars)
        public_key_path = config.paths('ssh_public_key')
        live_cluster.inject_public_ssh_key(public_key_path)
