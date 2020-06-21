from dcluster.cluster import instance as cluster_instance


def get(cluster_name):
    '''
    Retrieves a handle for a deployed cluster given its name.
    Raises NotFromDcluster if the cluster is not found.
    '''
    return cluster_instance.DeployedCluster.from_docker(cluster_name)


def start_cluster(cluster_name):
    '''
    Finds stopped containers belonging to a cluster and starts them (docker start <container>).
    If there are no stopped containers, then fails with an error message.
    '''
    cluster = get(cluster_name)
    cluster.start()


def stop_cluster(cluster_name):
    '''
    Stops the containers of a deployed cluster given its name.
    Does not remove the containers, they can be started again with Docker if needed.
    Raises NotFromDcluster if the cluster is not found.
    '''
    cluster = get(cluster_name)
    cluster.stop()


def remove_cluster(cluster_name):
    '''
    Removes the containers of a deployed cluster given its name, also removes the network.
    As a consequence, the Docker instances are no longer available.
    Raises NotFromDcluster if the cluster is not found.
    '''
    cluster = get(cluster_name)
    cluster.remove()
