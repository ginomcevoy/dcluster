'''
Creates a C-class named network for a Docker cluster.
Two conditions for creation:
- The name must not exist beforehand
- The IP range must be available.
'''

import ipaddress
import logging
import unittest

from six.moves import input

from dcluster import config

from .docker_facade import DockerNaming, DockerNetworking, NetworkSubnetTaken

SUPERNET = config.networking('supernet')
CIDR_BITS = config.networking('cidr_bits')


def create(cluster_name):
    '''
    Convenience function that uses the default configuration.
    '''
    return DockerClusterNetworkFactory().create(cluster_name)


class ClusterNetwork(object):
    '''
    Defines the cluster network addresses based on a subnet (ipaddress.Network object).
    Encapsulates a docker network object once the network has been created in Docker
    (docker.models.networks.Network).
    '''

    def __init__(self, subnet, cluster_name):
        self.subnet = subnet
        self.all_ip_addresses = list(self.subnet.hosts())
        self.cluster_name = cluster_name
        self.__docker_network = None
        self.log = logging.getLogger()

    def gateway_ip(self):
        '''
        Returns a suitable gateway IP address for a subnet. We prefer to use the last available IP
        address in the subnet. E.g. 172.30.0.0/24 -> 172.30.0.254
        '''
        msg = 'subnet %s has %s available IPs'
        self.log.debug(msg % (self.subnet, len(self.all_ip_addresses)))
        return str(self.all_ip_addresses[-1])

    def head_ip(self):
        '''
        Returns a suitable IP address for a head node in the subnet.
        We prefer to use the second-to-last available IP address in the subnet (last is for the
        gateway). E.g. 172.30.0.0/24 -> 172.30.0.253
        '''
        return str(self.all_ip_addresses[-2])

    def compute_ips(self, count):
        '''
        Returns a tuple of IP addresses for the cluster.
        Since the gateway and head use IP addresses at the end of the subnet, we can
        use the first IP addresses.

        If there are not enough addresses available, ValueError is raised.
        '''
        # make sure there are enough, count two for gateway and head
        available_count = len(self.all_ip_addresses) - 2
        if count > available_count:
            msg = 'Not enough IP addresses avaiable in network %s, %s requested'
            raise NetworkSubnetTooSmall(msg % (self.ip_address(), count))

        compute_addresses = self.all_ip_addresses[:count]
        return [str(compute_address) for compute_address in compute_addresses]

    def ip_address(self):
        return str(self.subnet)

    @property
    def network_name(self):
        return DockerNaming.create_network_name(self.cluster_name)

    def as_dict(self):
        '''
        Returns a dictionary representation for the network, to be used as a cluster spec entry.
        '''
        return {
            'name': self.network_name,
            'address': self.ip_address(),
            'gateway': config.networking('gateway'),
            'gateway_ip': self.gateway_ip()
        }

    def __str__(self):
        return self.ip_address()

    @classmethod
    def from_first_subnet(cls, supernet, cidr_bits, cluster_name):
        '''
        Given a supernet, return the first ClusterNetwork. This subnet will start at the same
        address as the supernet, and have cidr_bits available.
        '''
        # get the first item yielded by the generator
        return next(cls.generator(supernet, cidr_bits, cluster_name))

    @classmethod
    def from_subnet_str(cls, subnet_str, cluster_name):
        subnet = ipaddress.ip_network(subnet_str)
        return ClusterNetwork(subnet, cluster_name)

    @classmethod
    def generator(cls, supernet, cidr_bits, cluster_name):
        '''
        Returns a generator of ClusterNetwork, based on the subnet generator for all possible
        subnets given the supernet and cidr_bits.
        '''
        # python2 wants unicode, python3 does not like using decode...
        if hasattr(supernet, 'decode'):
            supernet = supernet.decode('unicode-escape')

        # https://docs.python.org/3/library/ipaddress.html
        super_network = ipaddress.ip_network(supernet)
        logging.getLogger().debug('super network %s ' % super_network)
        possible_subnets = super_network.subnets(new_prefix=cidr_bits)

        # this will turn this function into a generator that yields instances of this class
        for subnet in possible_subnets:
            yield ClusterNetwork(subnet, cluster_name)


class DockerClusterNetwork(ClusterNetwork):
    '''
    Cluster network that encapsulates a docker network, once it has been created in Docker
    (docker.models.networks.Network).
    '''

    def __init__(self, cluster_network, docker_network):
        subnet = cluster_network.subnet
        cluster_name = cluster_network.cluster_name
        super(DockerClusterNetwork, self).__init__(subnet, cluster_name)
        self.docker_network = docker_network

        self.log = logging.getLogger()

    @classmethod
    def from_subnet_and_name(cls, subnet, cluster_name, docker_network):
        cluster_network = ClusterNetwork(subnet, cluster_name)
        return DockerClusterNetwork(cluster_network, docker_network)

    @property
    def id(self):
        return self.docker_network.id

    @property
    def containers(self):
        return self.docker_network.containers

    def remove(self):
        self.docker_network.remove()
        self.log.debug('Removed network %s of cluster %s' % (self.network_name, self.cluster_name))

    def container_name(self, hostname):
        return DockerNaming.create_container_name(self.cluster_name, hostname)


class DockerClusterNetworkFactory:

    def __init__(self, supernet=SUPERNET, cidr_bits=CIDR_BITS):
        self.supernet = supernet
        self.cidr_bits = cidr_bits

    def validate_network_name(self, network_name):
        used_names = [network.name for network in DockerNetworking.all_docker_networks()]
        if network_name in used_names:
            raise NameExistsException('Network name is already in use: %s' % network_name)

        # name is available, return it to be nice
        return network_name

    def cluster_network_candidates(self, cluster_name):
        return ClusterNetwork.generator(self.supernet, self.cidr_bits, cluster_name)

    def attempt_create(self, cluster_network):
        '''
        Tries to create a named network.
        Returns a tuple with the Docker network and the subnet (ipaddress object) that was used
        to create said network.

        If the name exists, NameExistsException is raised.
        If the name is (apparently) available but the network creation fails,
        NetworkSubnetTaken is raised.

        Subject to race conditions in the name query, but since we try multiple times this should
        not be a major issue.
        '''

        # validate name to have one less reason that network creation fails
        self.validate_network_name(cluster_network.network_name)

        # this will raise NetworkSubnetTaken if the network is not available
        docker_network = DockerNetworking.create_network(cluster_network)

        # this encapsulates docker network
        docker_cluster_network = DockerClusterNetwork(cluster_network, docker_network)
        return docker_cluster_network

    def create(self, cluster_name):
        '''
        Calls 'attempt_create' iteratively until a network is created, or until
        all possible subnets have been exhausted. Returns DockerClusterNetwork instance

        If the cluster_name exists, NameExistsException is raised.
        If it is not possible to create a network (all IP ranges for the specified main network
        are taken) then NoNetworkSubnetsAvaialble is raised.
        '''
        docker_cluster_network = None
        cluster_network_candidates = self.cluster_network_candidates(cluster_name)

        while docker_cluster_network is None:

            try:
                cluster_network_candidate = next(cluster_network_candidates)
                docker_cluster_network = self.attempt_create(cluster_network_candidate)
            except NetworkSubnetTaken:
                # this subnet is taken, keep trying
                continue

            except StopIteration:
                # there are no more subnets to try
                msg = 'No more subnets available for network %s and CIDR bits %s'
                raise NoNetworkSubnetsAvaialble(msg % (str(self.supernet),
                                                       str(self.cidr_bits)))

        return docker_cluster_network

    @classmethod
    def from_existing(cls, cluster_name):
        '''
        Recreate a cluster network given that it exists in Docker.
        '''
        docker_network = DockerNetworking.find_network(cluster_name)
        subnet = DockerNetworking.get_subnet(docker_network)
        cluster_network = ClusterNetwork(subnet, cluster_name)
        return DockerClusterNetwork(cluster_network, docker_network)


class TestDockerClusterNetworkFactory(unittest.TestCase):

    def test_create_network_then_try_creating_it_again(self):

        supernet = '172.31.0.0/16'
        cidr_bits = 17
        network_factory = DockerClusterNetworkFactory(supernet, cidr_bits)

        print('*** test_create_network_then_try_creating_it_again ***')
        print('This test will use the main network %s' % supernet)

        first_name = 'shouldbenew'
        sg = network_factory.cluster_network_candidates(first_name)
        first_subnet = next(sg)

        print('About to create Docker network: %s' % str(first_subnet))
        print('Make sure that this network does not exist in Docker!')

        input('Press Enter to continue')

        # create it, should not raise error because the network name and subnet are available
        network_factory.validate_network_name(first_name)
        cluster_network = network_factory.attempt_create(first_subnet)

        second_name = 'shouldalsobenew'
        first_subnet.cluster_name = second_name

        print('Created the first network, now try to create another one with same subnet')
        input('Expected error message: 403 Client Error: Forbidden \
("Pool overlaps with other one on this address space")')

        # create another network with the same subnet, now we should get an error
        with self.assertRaises(NetworkSubnetTaken):
            network_factory.attempt_create(first_subnet)

        # try to clean up (remove first network)
        cluster_network.remove()
        print('Removed first network %s' % str(first_subnet))

    def test_create_until_no_more_available(self):

        supernet = '172.31.0.0/16'
        cidr_bits = 17
        network_factory = DockerClusterNetworkFactory(supernet, cidr_bits)

        print('*** test_create_until_no_more_available ***')
        print('This test will use the main network %s and create two subnets' % supernet)
        print('Make sure there are no test networks in Docker!')
        input('Press Enter to continue')

        print('About to create first network, this should succeed')
        input('Press Enter to continue')
        first_network = network_factory.create('shouldbenew1')

        print('Created first network %s' % str(first_network))
        print('About to create second network, this should succeed')
        input('Press Enter to continue')

        second_network = network_factory.create('shouldbenew2')
        print('Created network %s' % str(second_network))

        print('About to try and create another network, this should fail')
        input('Press Enter to continue')

        with self.assertRaises(NoNetworkSubnetsAvaialble):
            network_factory.create('shouldbenew3')

        # try to clean up
        print('Failed as expected, cleaning up...')
        first_network.remove()
        second_network.remove()


class NameExistsException(Exception):
    '''
    Expected to be raised when a network already exists with a specified name.
    Should inform the user and exit.
    '''
    pass


class NoNetworkSubnetsAvaialble(Exception):
    '''
    Expected to be raised when no network subnets are available by Docker.
    Should inform the user and exit.
    '''
    pass


class NetworkSubnetTooSmall(Exception):
    '''
    Expected to be raised when the available subnet is not large enough to fit the specified
    cluster (too many compute ndoes).
    Should inform the user and exit.
    '''
    pass


if __name__ == '__main__':
    # tests that create actual Docker networks!
    unittest.main()
