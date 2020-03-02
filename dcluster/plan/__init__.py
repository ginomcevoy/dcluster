from collections import namedtuple


SimpleCreationRequest = namedtuple('SimpleCreationRequest', ['name', 'compute_count', 'flavor'])

SimplePlannedNode = namedtuple('SimplePlannedNode', 'hostname, container, image, ip_address, role')

ExtendedPlannedNode = namedtuple('ExtendedPlannedNode',
                                 'hostname, container, image, ip_address, role, volumes, \
                                  static_text')

# after plannednode to avoid circular dep
from .simple import SimpleClusterPlan
from .extended import ExtendedClusterPlan


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
