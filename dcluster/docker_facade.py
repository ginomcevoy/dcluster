'''
Facade (simple API) for Docker python API.

Stores the singleton for a client connection to Docker.
Requires the user to be in the 'docker' group.
'''

import docker
import ipaddress
import logging

from operator import attrgetter

from . import config

__docker_client = None


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
    def logger(cls):
        if not hasattr(cls, 'log'):
            cls.log = logging.getLogger()
        return cls.log

    @classmethod
    def create_network_name(cls, cluster_name):
        '''
        Single place to define how network name is built based on cluster name.
        '''
        return '-'.join((config.networking('prefix'), cluster_name))

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

        network_name_is_string = isinstance(network_name, str) or isinstance(network_name, unicode)
        assert network_name_is_string, 'Could not understand %s' % network_name

        # now we have a string, dcluster networks are preceded by the prefix
        prefix = config.networking('prefix')
        cls.logger().debug('Looking in %s for %s' % (network_name, prefix))

        if network_name.find(prefix) != 0:
            # this is not a dcluster network
            raise NotFromDcluster()

        # this is a dcluster string
        return network_name[(len(config.networking('prefix')) + 1):]

    @classmethod
    def is_dcluster_network(cls, network):
        '''
        Returns true iff a network belongs to dcluster.
        This is equivalent of finding the dcluster name of the network.
        '''
        try:
            cls.deduce_cluster_name(network)
        except Exception as e:
            cls.logger().debug('Not a dcluster network: %s' % network.name)
            cls.logger().debug(e)
            return False

        return True

    @classmethod
    def create_container_name(cls, cluster_name, hostname):
        '''
        Single place to define how container names are built based on cluster name and hostname.
        '''
        return '-'.join((cluster_name, hostname))


class ClusterNode(object):
    '''
    Encapsulates docker-specific implementation of a container and its attributes.
    Assumes it is part of a docker cluster.
    '''

    def __init__(self, docker_container, docker_network):
        self.docker_container = docker_container
        self.docker_network = docker_network

    @property
    def hostname(self):
        return self.docker_container.attrs['Config']['Hostname']

    @property
    def ip_address(self):
        '''
        Finds the IP address of a container that corresponds to a specific docker network.
        '''
        container_networks = self.docker_container.attrs['NetworkSettings']['Networks']
        return container_networks[self.docker_network.name]['IPAddress']

    @property
    def container(self):
        return self.docker_container

    @classmethod
    def find_for_cluster(cls, cluster_name, docker_network=None):
        if not docker_network:
            docker_network = DockerNetworking.find_network(cluster_name)

        # get internal containers
        client = get_client()
        all_docker_containers = client.containers.list()

        # match the network, create the instances
        # Finding containers for a network should be as easy as docker_network.containers,
        # but the API is returning an empty list sometimes...
        cluster_containers = [
            ClusterNode(docker_container, docker_network)
            for docker_container
            in all_docker_containers
            if docker_network.name in docker_container.attrs['NetworkSettings']['Networks']
        ]

        return sorted(cluster_containers, key=attrgetter('ip_address'))


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
        Returns a list of all dcluster networks, as docker network instances.
        (docker.models.networks.Network)

        See is_dcluster_network() for assumption.
        '''
        # get Docker networks, use logic in is_dcluster_network()
        # to determine which belong to dcluster
        all_networks = cls.all_docker_networks()
        cls.logger().debug(all_networks)
        return [
            network
            for network
            in all_networks
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
