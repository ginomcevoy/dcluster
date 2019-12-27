'''
Facade (simple API) for Docker python API.

Stores the singleton for a client connection to Docker.
Requires the user to be in the 'docker' group.
'''

import docker
import subprocess

from . import cluster


__docker_client = None


class NetworkSubnetTaken(Exception):
    '''
    Expected to be raised when a network subnet is already taken by Docker.
    Should be used to indicate that another subnet is to be tried.
    '''
    pass


def get_client():
    global __docker_client
    if __docker_client is None:
        __docker_client = docker.from_env()
    return __docker_client


def networks():
    client = get_client()
    return client.networks.list()


def create_network(cluster_network):
    client = get_client()
    try:
        # from docker.models.networks.create() help
        gateway_ip = cluster_network.gateway_ip()
        subnet = cluster_network.fqdn()
        network_name = cluster_network.network_name()
        ipam_pool = docker.types.IPAMPool(subnet=subnet, gateway=gateway_ip)
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
        docker_network = client.networks.create(network_name,
                                                driver='bridge',
                                                attachable=True,
                                                ipam=ipam_config)

    except docker.errors.APIError as e:
        # network creation failed, assume that subnet was taken
        print(str(e))
        raise NetworkSubnetTaken

    return docker_network


def get_ip_address_for_cluster_node(cluster_name, hostname):
    network_name = cluster.get_network_name(cluster_name)
    container_name = cluster.get_container_name(cluster_name, hostname)

    client = get_client()
    container = client.containers.get(container_name)

    # we assume that the container was created using DockerClusterNetwork
    container_networks = container.attrs['NetworkSettings']['Networks']
    docker_cluster_network = container_networks[network_name]
    return docker_cluster_network['IPAddress']


def ssh_to_cluster_node(cluster_name, hostname):
    ip_address = get_ip_address_for_cluster_node(cluster_name, hostname)
    ssh_command = '/usr/bin/ssh -o "StrictHostKeyChecking=no" -o "GSSAPIAuthentication=no" \
-o "UserKnownHostsFile /dev/null" -o "LogLevel ERROR %s"'

    target = 'root@%s' % ip_address
    full_ssh_command = ssh_command % target
    subprocess.check_output(full_ssh_command, shell=True)
