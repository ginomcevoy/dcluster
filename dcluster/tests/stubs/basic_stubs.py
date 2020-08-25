from dcluster.config import flavor_config
from dcluster.cluster.request import BasicCreationRequest
from dcluster.cluster.planner import BasicClusterPlan, basic_plan_data
from dcluster.node.planner import BasicNodePlanner

from . import infra_stubs


def basic_config():
    return flavor_config.cluster_config_for_flavor('simple')


def basic_request_stub(cluster_name, compute_count):
    return BasicCreationRequest(cluster_name, compute_count, 'simple', [], [], [])


def basic_plan_data_stub(cluster_name, compute_count):
    request = basic_request_stub(cluster_name, compute_count)
    return basic_plan_data(basic_config(), request)


def basic_node_planner_stub(cluster_name, subnet_str):
    network = infra_stubs.network_stub(cluster_name, subnet_str)
    return BasicNodePlanner(network)


def basic_cluster_plan_stub(cluster_name, subnet_str, compute_count):
    creation_request = basic_request_stub(cluster_name, compute_count)
    cluster_network = infra_stubs.network_stub(cluster_name, subnet_str)
    return BasicClusterPlan.create(creation_request, basic_config(), cluster_network)
