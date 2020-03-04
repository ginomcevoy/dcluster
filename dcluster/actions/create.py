from . import display

from dcluster import config, cluster, dansible, runtime

from dcluster.infra import networking


def create_simple_cluster(creation_request):
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
    cluster_plan = cluster.create_plan(creation_request, cluster_config, cluster_network)

    # get the blueprints with plans for all nodes
    cluster_blueprints = cluster_plan.create_blueprints()

    # deploy the cluster
    renderer = runtime.get_renderer(creation_request)
    composer_workpath = config.composer_workpath(creation_request.name)
    deployer = runtime.DockerComposeDeployer(composer_workpath)

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
