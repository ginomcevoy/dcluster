from dcluster.config import profile_config
from dcluster.cluster.request import DefaultCreationRequest
from dcluster.cluster.planner import DefaultClusterPlan, user_plan_data
from dcluster.node.planner import BasicNodePlanner

from . import infra_stubs


def simple_config():
    return profile_config.cluster_config_for_profile('simple')


def default_request_stub(cluster_name, compute_count):
    return DefaultCreationRequest(cluster_name, compute_count, 'simple', [], [], [])


def user_plan_data_stub(cluster_name, compute_count):
    request = default_request_stub(cluster_name, compute_count)
    return user_plan_data(simple_config(), request)


def basic_node_planner_stub(cluster_name, subnet_str):
    network = infra_stubs.network_stub(cluster_name, subnet_str)
    return BasicNodePlanner(network)


def default_cluster_plan_stub(cluster_name, subnet_str, compute_count):
    creation_request = default_request_stub(cluster_name, compute_count)
    cluster_network = infra_stubs.network_stub(cluster_name, subnet_str)
    return DefaultClusterPlan.create(creation_request, simple_config(), cluster_network)
