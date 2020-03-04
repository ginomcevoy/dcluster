import ipaddress

from dcluster.infra import networking


def network_stub(cluster_name, subnet_str):
    subnet = ipaddress.ip_network(subnet_str)
    return networking.ClusterNetwork(subnet, cluster_name)
