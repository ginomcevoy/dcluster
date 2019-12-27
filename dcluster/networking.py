'''
Creates a C-class named network for a Docker cluster.
Two conditions for creation:
- The name must not exist beforehand
- The IP range must be available.
'''

import ipaddress
import unittest

from six.moves import input

from . import cluster
from . import docker_facade

from . import SUPERNET, CIDR_BITS
from . import HOSTNAME, TYPE
from . import HEAD_NAME, HEAD_TYPE, GATEWAY_NAME, GATEWAY_TYPE
from . import COMPUTE_PREFIX, COMPUTE_SUFFIX_LEN, COMPUTE_TYPE, CONTAINER


def create(cluster_name):
    '''
    Convenience function that uses the default configuration.
    '''
    return DockerClusterNetworkFactory().create(cluster_name)


class ClusterNetwork:
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

    def gateway_ip(self):
        '''
        Returns a suitable gateway IP address for a subnet. We prefer to use the last available IP
        address in the subnet. E.g. 172.30.0.0/24 -> 172.30.0.254
        '''
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
            raise NetworkSubnetTooSmall(msg % (self.fqdn(), count))

        compute_addresses = self.all_ip_addresses[:count]
        return [str(compute_address) for compute_address in compute_addresses]

    def fqdn(self):
        return str(self.subnet)

    def network_name(self):
        return cluster.get_network_name(self.cluster_name)

    def __str__(self):
        return self.fqdn()

    @classmethod
    def from_first_subnet(cls, supernet, cidr_bits, cluster_name):
        '''
        Given a supernet, return the first ClusterNetwork. This subnet will start at the same
        address as the supernet, and have cidr_bits available.
        '''
        # get the first item yielded by the generator
        return next(cls.generator(supernet, cidr_bits, cluster_name))

    @classmethod
    def generator(cls, supernet, cidr_bits, cluster_name):
        '''
        Returns a generator of ClusterNetwork, based on the subnet generator for all possible
        subnets given the supernet and cidr_bits.
        '''
        # https://docs.python.org/3/library/ipaddress.html
        super_network = ipaddress.ip_network(supernet)
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
        return self.docker_network.remove()

    def container_name(self, hostname):
        return cluster.get_container_name(self.cluster_name, hostname)

    def build_host_details(self, compute_count):
        '''
        Creates the host details that are needed for an Ansible inventory.
        Since we are only building a single type of cluster, we can leave this here.

        A cluster always has a single head (slurmctld), and zero or more compute nodes, depending
        on compute_count.

        Also add the host of the containers as the gateway.

        Example output: for compute_count = 3, add a head node and 3 compute nodes:
        host_details = {
            '172.30.0.253': {
                'hostname': 'slurmctld',
                'container': 'mycluster-slurmctld',
                'type': 'head'
            },
            '172.30.0.1': {
                'hostname': 'node001',
                'container': 'mycluster-node001',
                'type': 'compute'
            },
            '172.30.0.2': {
                'hostname': 'node002',
                'container': 'mycluster-node002',
                'type': 'compute'
            },
            '172.30.0.3': {
                'hostname': 'node003',
                'container': 'mycluster-node003',
                'type': 'compute'
            }
            '172.30.0.254': {
                'hostname': 'gateway',
                'type': 'gateway'
            }
        }

        TODO move this to a better place?
        '''
        # always have a head and a gateway
        host_details = {
            self.head_ip(): {
                HOSTNAME: HEAD_NAME,
                CONTAINER: self.container_name(HEAD_NAME),
                TYPE: HEAD_TYPE
            },
            self.gateway_ip(): {
                HOSTNAME: GATEWAY_NAME,
                TYPE: GATEWAY_TYPE
            }
        }

        # add compute nodes, should raise NetworkSubnetTooSmall if there are not enough IPs
        compute_ips = self.compute_ips(compute_count)
        for index, compute_ip in enumerate(compute_ips):
            suffix_str = '{0:0%sd}' % str(COMPUTE_SUFFIX_LEN)
            suffix = suffix_str.format(index + 1)
            hostname = COMPUTE_PREFIX + suffix
            host_details[compute_ip] = {
                HOSTNAME: hostname,
                CONTAINER: self.container_name(hostname),
                TYPE: COMPUTE_TYPE
            }

        return host_details


class DockerClusterNetworkFactory:

    def __init__(self, supernet=SUPERNET, cidr_bits=CIDR_BITS):
        self.supernet = supernet
        self.cidr_bits = cidr_bits

    def validate_network_name(self, network_name):
        used_names = [network.name for network in docker_facade.networks()]
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
        self.validate_network_name(cluster_network.network_name())

        # this will raise NetworkSubnetTaken if the network is not available
        docker_network = docker_facade.create_network(cluster_network)

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
            except docker_facade.NetworkSubnetTaken:
                # this subnet is taken, keep trying
                continue

            except StopIteration:
                # there are no more subnets to try
                msg = 'No more subnets available for network %s and CIDR bits %s'
                raise NoNetworkSubnetsAvaialble(msg % (str(self.supernet),
                                                       str(self.cidr_bits)))

        return docker_cluster_network


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
        with self.assertRaises(docker_facade.NetworkSubnetTaken):
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
