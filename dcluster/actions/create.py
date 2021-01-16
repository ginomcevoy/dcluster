from . import display

from dcluster import cluster, dansible, runtime

from dcluster.config import main_config, dansible_config
from dcluster.infra import networking

from dcluster.util import fs as fs_util


def create_default_cluster(creation_request):
    '''
    Creates a new default cluster, the request must have:
    - name
    - compute_count
    - profile

    other optional arguments:
    - playbooks
    - extra_vars_list
    '''
    # ensure that user-specified profile paths exist before attempting anything
    fs_util.check_directories_exist(creation_request.profile_paths)

    # go ahead and create the network using Docker
    cluster_network = networking.create(creation_request.name)

    # develop the cluster plan given request
    cluster_plan = cluster.create_plan(creation_request, cluster_network)

    # get the blueprints with plans for all nodes
    cluster_blueprints = cluster_plan.create_blueprints()

    # deploy the cluster
    renderer = runtime.get_renderer(creation_request)
    composer_workpath = main_config.composer_workpath(creation_request.name)
    deployer = runtime.DockerComposeDeployer(composer_workpath)

    cluster_blueprints.deploy(renderer, deployer)

    # create the Ansible inventory now, too hard later
    cluster_name = creation_request.name
    inventory_workpath = dansible_config.inventory_workpath(cluster_name)
    (_, inventory_file) = dansible.create_inventory(cluster_blueprints.as_dict(),
                                                    inventory_workpath)

    # show newly created
    live_cluster = display.show_cluster(creation_request.name)

    if main_config.prefs('inject_ssh_public_keys_to_root'):
        # inject SSH public key to all containers for password-less SSH

        # public_key_with_shell_vars = main_config.paths('ssh_public_key')
        # public_key_path = fs_util.evaluate_shell_path(public_key_with_shell_vars)
        public_key_paths = main_config.paths('ssh_public_keys')
        for public_key_path in public_key_paths:
            live_cluster.inject_public_ssh_key(public_key_path)

    # fix for containers running /sbin/init
    live_cluster.fix_init_if_needed()

    # run requested Ansible playbooks with optional extra vars
    for playbook in creation_request.playbooks:
        dansible.run_playbook(cluster_name, playbook, inventory_file,
                              creation_request.extra_vars_list)
