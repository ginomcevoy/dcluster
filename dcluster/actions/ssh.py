from . import manage


def ssh(cluster_name, username, hostname):
    '''
    Performs SSH to a node in the cluster. The target can have username@hostname, or only hostname
    (uses default ssh_user)
    '''
    # delegate ssh to cluster object
    # TODO bring some SSH stuff here
    cluster = manage.get(cluster_name)
    cluster.ssh_to_node(username, hostname)


def scp(cluster_name, username, hostname, target_dir, files):
    '''
    Performs SSH to a node in the cluster. The target can have username@hostname, or only hostname
    (uses default ssh_user)
    '''
    # delegate scp to cluster object
    # TODO evaluate "-r" here
    cluster = manage.get(cluster_name)
    cluster.scp_to_node(username, hostname, target_dir, files)
