from dcluster.cluster import simple as simple_cluster
from dcluster.plan import simple as simple_plan


def show_cluster(cluster_name):

    cluster = simple_cluster.DeployedCluster.from_docker(cluster_name)
    formatter = simple_plan.SimpleFormatter()
    output = cluster.format(formatter)
    print(output)


def list_clusters():
    cluster_list = simple_cluster.DeployedCluster.list_all()
    print('\n'.join(cluster_list))
