'''
Facade (simple API) for Docker python API.

Stores the singleton for a client connection to Docker.
Requires the user to be in the 'docker' group.
'''

import docker
import ipaddress
import logging
import subprocess

from collections import namedtuple
from operator import attrgetter

__docker_client = None

DCLUSTER_NETWORK_PREFIX = 'dcluster'

Node = namedtuple('Node', ['hostname', 'ip_address', 'container'])


def get_client():
    global __docker_client
    if __docker_client is None:
        __docker_client = docker.from_env()
    return __docker_client


class NetworkSubnetTaken(Exception):
    '''
    Expected to be raised when a network subnet is already taken by Docker.
    Should be used to indicate that another subnet is to be tried.
    '''
    pass


class NotFromDcluster(Exception):
    '''
    Expected to be raised when a Docker element (network, container) does not belong to dcluster.
    Should be used when querying for a network/container by name but the item is not from dcluster.
    '''
    pass


class DockerNaming:

    @classmethod
    def create_network_name(cls, cluster_name):
        '''
        Single place to define how network name is built based on cluster name.
        '''
        return '-'.join((DCLUSTER_NETWORK_PREFIX, cluster_name))

    @classmethod
    def deduce_cluster_name(cls, network):
        '''
        Given a network name, try and find the cluster name. Raises NotFromDcluster if the
        network does not belong to dcluster.

        Works on cluster_network, docker network instance and the string.
        '''
        # default, assume string
        network_name = network

        if hasattr(network, 'network_name'):
            # assume ClusterNetwork instance
            network_name = network.network_name

        elif hasattr(network, 'name'):
            # assume Docker network instance
            network_name = network.name

        assert type(network_name) == str, 'Could not understand %s' % network_name

        # now we have a string, dcluster networks are preceded by the prefix
        if network_name.find(DCLUSTER_NETWORK_PREFIX) != 0:
            # this is not a dcluster network
            raise NotFromDcluster()

        # this is a dcluster string
        return network_name[(len(DCLUSTER_NETWORK_PREFIX) + 1):]

    @classmethod
    def is_dcluster_network(cls, network):
        '''
        Returns true iff a network belongs to dcluster.
        This is equivalent of finding the dcluster name of the network.
        '''
        try:
            cls.deduce_cluster_name(network)
        except Exception:
            # not a dcluster network
            return False

        return True

    @classmethod
    def create_container_name(cls, cluster_name, hostname):
        '''
        Single place to define how container names are built based on cluster name and hostname.
        '''
        return '-'.join((cluster_name, hostname))


class DockerNetworking:

    @classmethod
    def logger(cls):
        if not hasattr(cls, 'log'):
            cls.log = logging.getLogger()
        return cls.log

    @classmethod
    def all_docker_networks(cls):
        '''
        Returns a list of all Docker networks, whether they are created from dcluster or not.
        This returns docker network instances (docker.models.networks.Network)
        '''
        client = get_client()
        return client.networks.list()

    @classmethod
    def all_dcluster_networks(cls):
        '''
        Returns a list of all dcluster networks, as string. See is_dcluster_network() for
        assumption.
        '''
        # get Docker networks, use logic in is_dcluster_network()
        # to determine which belong to dcluster
        return [
            network
            for network
            in cls.all_docker_networks()
            if DockerNaming.is_dcluster_network(network)]

    @classmethod
    def find_network(cls, cluster_name):
        '''
        Returns a docker.models.networks.Network for the network name.
        Assumes it exists in dcluster.
        '''
        network_name = DockerNaming.create_network_name(cluster_name)
        networks = cls.all_dcluster_networks()

        with_name = None
        for network in networks:
            if network.name == network_name:
                with_name = network
                break

        if not with_name:
            raise NotFromDcluster()

        return with_name

    @classmethod
    def get_subnet(cls, docker_network):
        '''
        Subnet of docker network, as a ipaddress.IPv4Network object.
        '''
        subnet_str = docker_network.attrs['IPAM']['Config'][0]['Subnet']
        return ipaddress.ip_network(subnet_str)

    @classmethod
    def create_network(cls, cluster_network):
        client = get_client()
        try:
            # from docker.models.networks.create() help
            gateway_ip = cluster_network.gateway_ip()
            subnet = cluster_network.ip_address()
            network_name = cluster_network.network_name
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

    @classmethod
    def find_nodes_for_cluster(cls, cluster_name, docker_network=None):
        '''
        Finds all nodes that belong to a docker network, as Node namedtuple.
        '''
        if not docker_network:
            docker_network = cls.find_network(cluster_name)

        cls.logger().debug(docker_network)

        # get containers first, then build Node for each of them
        containers = cls.find_containers_for_network(docker_network)
        nodes = [
            cls.create_node_for_container(container, docker_network)
            for container
            in containers
        ]
        return sorted(nodes, key=attrgetter('ip_address'))

    @classmethod
    def find_containers_for_network(cls, docker_network):
        '''
        Returns a list of containers that belong to a docker network.
        This should be as easy as docker_network.containers, but the API is returning
        an empty list sometimes.
        '''
        client = get_client()
        containers = client.containers.list()
        return [
            container
            for container
            in containers
            if docker_network.name in container.attrs['NetworkSettings']['Networks']
        ]

    @classmethod
    def container_ip_address(cls, container, docker_network):
        '''
        Finds the IP address of a container that corresponds to a specific docker network.
        '''
        container_networks = container.attrs['NetworkSettings']['Networks']
        return container_networks[docker_network.name]['IPAddress']

    @classmethod
    def create_node_for_container(cls, container, docker_network):
        '''
        Creates a Node namedtuple instance using a Docker container object
        (docker.models.containers.Container)
        '''
        hostname = container.attrs['Config']['Hostname']
        ip_address = cls.container_ip_address(container, docker_network)

        return Node(hostname, ip_address, container)
