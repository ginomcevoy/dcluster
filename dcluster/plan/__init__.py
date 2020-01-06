from collections import namedtuple


SimpleCreationRequest = namedtuple('SimpleCreationRequest', ['name', 'compute_count', 'flavor'])

PlannedNode = namedtuple('PlannedNode', 'hostname, container, image, ip_address, role')

# after plannednode to avoid circular dep
from .simple import SimpleClusterPlan


def create_plan(creation_request, flavor_config, cluster_network):
    '''
    Build plan based on user request, existing configuration and a existing network.
    The parameters in the user request are merged with existing configuration.
    '''
    # only simple for now
    return SimpleClusterPlan.create(creation_request, flavor_config, cluster_network)
