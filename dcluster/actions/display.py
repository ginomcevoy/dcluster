from dcluster.cluster import instance, format


def show_cluster(cluster_name):

    cluster = instance.DeployedCluster.from_docker(cluster_name)
    formatter = format.SimpleFormatter()
    output = cluster.format(formatter)
    print(output)
    return cluster


def list_clusters():
    cluster_list = instance.DeployedCluster.list_all()
    print('\n'.join(cluster_list))
