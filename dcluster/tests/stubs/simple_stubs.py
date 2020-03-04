from dcluster import config

from dcluster.cluster.request import SimpleCreationRequest
from dcluster.cluster.planner import SimpleClusterPlan, simple_plan_data
from dcluster.node.planner import SimpleNodePlanner

from . import base_stubs


def simple_config():
    return config.for_cluster('simple')


def simple_request_stub(cluster_name, compute_count):
    return SimpleCreationRequest(cluster_name, compute_count, 'simple')


def simple_plan_data_stub(cluster_name, compute_count):
    request = simple_request_stub(cluster_name, compute_count)
    return simple_plan_data(simple_config(), request)


def simple_node_planner_stub(cluster_name, subnet_str):
    network = base_stubs.network_stub(cluster_name, subnet_str)
    return SimpleNodePlanner(network)


def simple_cluster_plan_stub(cluster_name, subnet_str, compute_count):
    creation_request = simple_request_stub(cluster_name, compute_count)
    cluster_network = base_stubs.network_stub(cluster_name, subnet_str)
    return SimpleClusterPlan.create(creation_request, simple_config(), cluster_network)
