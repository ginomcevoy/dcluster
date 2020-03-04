from dcluster.cluster import instance as cluster_instance


def get(cluster_name):
    return cluster_instance.DeployedCluster.from_docker(cluster_name)


def stop_cluster(cluster_name):
    cluster = get(cluster_name)
    cluster.stop()


def remove_cluster(cluster_name):
    cluster = get(cluster_name)
    cluster.remove()
