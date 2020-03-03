from dcluster import config

from dcluster.cluster.request import SimpleCreationRequest
from dcluster.plan.extended import ExtendedNodePlanner, ExtendedClusterPlan
from dcluster.plan.simple import simple_plan_data


from . import base_stubs


def slurm_config():
    '''
    Use slurm configuration with volumes and static parameters
    '''
    return config.for_cluster('slurm')


def simple_slurm_request_stub(cluster_name, compute_count):
    '''
    Use the simple request (no additional parameters) but ask for slurm flavor
    '''
    return SimpleCreationRequest(cluster_name, compute_count, 'slurm')


def slurm_plan_data_stub(cluster_name, compute_count):
    '''
    This extended data plan uses a simple slurm request, which already pulls the
    volumes and static text. The merge of the configuration and the request is kept 'simple'
    '''
    request = simple_slurm_request_stub(cluster_name, compute_count)
    return simple_plan_data(slurm_config(), request)


def extended_node_planner_stub(cluster_name, subnet_str):
    '''
    This extended node planner is meant to use the slurm_plan_data in tests.
    '''
    network = base_stubs.network_stub(cluster_name, subnet_str)
    return ExtendedNodePlanner(network)


def slurm_cluster_plan_stub(cluster_name, subnet_str, compute_count):
    creation_request = simple_slurm_request_stub(cluster_name, compute_count)
    cluster_network = base_stubs.network_stub(cluster_name, subnet_str)
    return ExtendedClusterPlan.create(creation_request, slurm_config(), cluster_network)
