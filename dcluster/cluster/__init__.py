from .planner import DefaultClusterPlan
# BasicClusterPlan, ExtendedClusterPlan

from dcluster.config import profile_config


# this matches the type to a plan
plans_by_type = {
    'default': DefaultClusterPlan
}


def create_plan(creation_request, cluster_network):
    '''
    Build plan based on user request, existing configuration and a existing network.
    The parameters in the user request are merged with existing configuration.
    '''

    # find the configuration given the profile
    # let the user specify additional places to look for profile files
    cluster_config = profile_config.cluster_config_for_profile(creation_request.profile,
                                                               creation_request.profile_paths)

    # the configuration specifies the type of cluster, use plans_by_type to match
    plan_for_type = plans_by_type[cluster_config['cluster_type']]

    # call the factory method of the right class
    return plan_for_type.create(creation_request, cluster_config, cluster_network)
