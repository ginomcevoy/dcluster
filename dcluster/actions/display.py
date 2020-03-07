from dcluster.cluster import instance, format


def show_cluster(cluster_name):
    '''
    Shows information about an existing cluster.
    Raises NotFromDcluster if the cluster is not found.
    '''
    cluster = instance.DeployedCluster.from_docker(cluster_name)
    formatter = format.TextFormatterBasic()
    output = cluster.format(formatter)
    print(output)
    return cluster


def list_clusters():
    '''
    Outputs the names of the clusters that are currently online.
    '''
    cluster_list = instance.DeployedCluster.list_all()
    print('\n'.join(cluster_list))
