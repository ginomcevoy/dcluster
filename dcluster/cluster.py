

def get_container_name(cluster_name, hostname):
    '''
    Single place to define how container names are built based on cluster name and hostname.
    '''
    return '-'.join((cluster_name, hostname))


def get_network_name(cluster_name):
    '''
    Single place to define how network name is built based on cluster name.
    '''
    return cluster_name
