from dcluster.config import profile_config

from dcluster.cluster.request import DefaultCreationRequest
from dcluster.cluster.planner import user_plan_data, DefaultClusterPlan
from dcluster.node.planner import DefaultNodePlanner


from . import infra_stubs


def slurm_config():
    '''
    Use slurm configuration with volumes and static parameters
    '''
    return profile_config.cluster_config_for_profile('slurm')


def basic_slurm_request_stub(cluster_name, compute_count):
    '''
    Use the basic request (no additional parameters) but ask for slurm profile
    '''
    return DefaultCreationRequest(cluster_name, compute_count, 'slurm', [], [], [])


def slurm_plan_data_stub(cluster_name, compute_count):
    '''
    This extended data plan uses a basic slurm request, which already pulls the
    volumes and static text. The merge of the configuration and the request is kept 'basic'
    '''
    request = basic_slurm_request_stub(cluster_name, compute_count)
    return user_plan_data(slurm_config(), request)


def extended_node_planner_stub(cluster_name, subnet_str):
    '''
    This extended node planner is meant to use the slurm_plan_data in tests.
    '''
    network = infra_stubs.network_stub(cluster_name, subnet_str)
    return DefaultNodePlanner(network)


def basic_slurm_cluster_plan_stub(cluster_name, subnet_str, compute_count):
    creation_request = basic_slurm_request_stub(cluster_name, compute_count)
    cluster_network = infra_stubs.network_stub(cluster_name, subnet_str)
    return DefaultClusterPlan.create(creation_request, slurm_config(), cluster_network)
