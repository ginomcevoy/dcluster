from .planner import SimpleClusterPlan, ExtendedClusterPlan


def create_plan(creation_request, flavor_config, cluster_network):
    '''
    Build plan based on user request, existing configuration and a existing network.
    The parameters in the user request are merged with existing configuration.
    '''
    if creation_request.flavor == 'simple':
        return SimpleClusterPlan.create(creation_request, flavor_config, cluster_network)
    elif creation_request.flavor == 'build':
        return SimpleClusterPlan.create(creation_request, flavor_config, cluster_network)
    elif creation_request.flavor == 'slurm':
        return ExtendedClusterPlan.create(creation_request, flavor_config, cluster_network)
