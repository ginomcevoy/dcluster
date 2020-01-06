from dcluster.cluster import simple as simple_cluster


def get(cluster_name):
    return simple_cluster.DeployedCluster.from_docker(cluster_name)


def stop_cluster(cluster_name):
    cluster = get(cluster_name)
    cluster.stop()


def remove_cluster(cluster_name):
    cluster = get(cluster_name)
    cluster.remove()


def ssh(cluster_name, hostname):
    cluster = get(cluster_name)
    cluster.ssh_to_node(hostname)
