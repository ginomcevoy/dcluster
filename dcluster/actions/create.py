import os

from dcluster import config, cluster, networking, plan

from dcluster.actions import display


def interpret_args(args):
    cluster_name = args.cluster_name
    flavor = args.flavor
    count = int(args.compute_count)
    by_flavor = {
        'simple': plan.SimpleCreationRequest(cluster_name, count, flavor)
    }
    return by_flavor[flavor]


def create_cluster(creation_request, basepath):
    '''
    Creates a new cluster based on a creation request, it should at least have the flavor.
    '''
    create_by_flavor = {
        'simple': create_simple_cluster
    }
    return create_by_flavor[creation_request.flavor](creation_request, basepath)


def create_simple_cluster(creation_request, basepath):
    '''
    Creates a new simple cluster, the request should have:
    - name
    - compute_count
    - flavor (should be 'simple' for now)
    '''
    # go ahead and create the network using Docker
    cluster_network = networking.create(creation_request.name)

    # develop the cluster plan given request + config
    simple_config = config.for_cluster(creation_request.flavor)
    cluster_plan = plan.create_plan(creation_request, simple_config, cluster_network)

    # get the blueprints with plans for all nodes
    cluster_blueprints = cluster_plan.create_blueprints()

    renderer = cluster.get_renderer(creation_request)
    compose_path = os.path.join(basepath, creation_request.name)  # eww?
    deployer = cluster.DockerComposeDeployer(compose_path)

    cluster_blueprints.deploy(renderer, deployer)

    # show newly created
    display.show_cluster(creation_request.name)
