from . import simple

cluster_builders = {
    'ClusterRequestSimple': simple.ClusterBuilderSimple()
}


def create(cluster_request, basepath):
    '''
    Create a docker cluster based on a request. Will instantiate a builder and ask it to build
    the cluster.
    '''
    builder = cluster_builders[type(cluster_request).__name__]
    return builder.build(cluster_request, basepath)
