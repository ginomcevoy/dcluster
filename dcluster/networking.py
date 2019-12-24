'''
Creates a C-class named network for a Docker cluster.
Two conditions for creation:
- The name must not exist beforehand
- The IP range must be available.
'''

import docker
import ipaddress
import unittest

from six.moves import input

from . import SUPERNET, CIDR_BITS
from . import connect


class SubnetDetails:
    '''
    Defines the cluster network addresses based on a subnet (ipaddress.Network object).
    '''

    def __init__(self, subnet, name=None):
        self.subnet = subnet
        self.all_ip_addresses = list(self.subnet.hosts())
        self.name = name

    def gateway_ip(self):
        '''
        Returns a suitable gateway IP address for a subnet. We prefer to use the last available IP
        address in the subnet. E.g. 172.30.0.0/24 -> 172.30.0.254
        '''
        return str(self.all_ip_addresses[-1])

    def controller_ip(self):
        '''
        Returns a suitable IP address for a controller node in the subnet.
        We prefer to use the second-to-last available IP address in the subnet (last is for the
        gateway). E.g. 172.30.0.0/24 -> 172.30.0.253
        '''
        return str(self.all_ip_addresses[-2])

    def compute_ips(self, count):
        '''
        Returns a tuple of IP addresses for the cluster.
        Since the gateway and controller use IP addresses at the end of the subnet, we can
        use the first IP addresses.

        If there are not enough addresses available, ValueError is raised.
        '''
        # make sure there are enough, count two for gateway and controller
        available_count = len(self.all_ip_addresses) - 2
        if count > available_count:
            msg = 'Not enough IP addresses avaiable in network %s, %s requested'
            raise NetworkSubnetTooSmall(msg % (self.subnet, count))

        compute_addresses = self.all_ip_addresses[:count]
        return [str(compute_address) for compute_address in compute_addresses]

    def __str__(self):
        return str(self.subnet)

    @classmethod
    def from_first_subnet(cls, supernet, cidr_bits, name=None):
        '''
        Given a supernet, return the first SubnetDetails. This subnet will start at the same
        address as the supernet, and have cidr_bits available.
        '''
        # get the first item yielded by the generator
        return next(cls.subnet_details_generator(supernet, cidr_bits, name))

    @classmethod
    def subnet_details_generator(cls, supernet, cidr_bits, name=None):
        '''
        Returns a generator of SubnetDetails, based on the subnet generator for all possible
        subnets given the supernet and cidr_bits.
        '''
        # https://docs.python.org/3/library/ipaddress.html
        super_network = ipaddress.ip_network(supernet)
        possible_subnets = super_network.subnets(new_prefix=cidr_bits)

        # this will turn this function into a generator that yields instances of this class
        for subnet in possible_subnets:
            yield SubnetDetails(subnet, name)


class CreateNetwork:

    def __init__(self, supernet=SUPERNET, cidr_bits=CIDR_BITS, client=None):
        if not client:
            client = connect.client()

        self.client = client
        self.supernet = supernet
        self.cidr_bits = cidr_bits

    def validate_name(self, name):
        used_names = [network.name for network in self.client.networks.list()]
        if name in used_names:
            raise NameExistsException('Network name is already in use: %s' % name)

        # name is available, return it to be nice
        return name

    def get_possible_subnet_details(self, name):
        return SubnetDetails.subnet_details_generator(self.supernet, self.cidr_bits, name)

    # @property
    # def subnet_generator(self):
    #     '''
    #     Generator for all subnets in the main network that have the specified prefix.
    #     '''
    #     # https://docs.python.org/3/library/ipaddress.html
    #     network = ipaddress.ip_network(self.main_network)
    #     possible_subnets = network.subnets(new_prefix=self.cidr_bits)
    #     return possible_subnets

    # def gateway_ip(self, subnet):
    #     '''
    #     Returns a suitable gateway IP address for a subnet. We prefer to use the last available IP
    #     address in the subnet. E.g. 172.30.0.0/24 -> 172.30.0.254
    #     '''
    #     all_ip_addresses = list(subnet.hosts())
    #     return all_ip_addresses[-1]

    # def controller_ip(self, subnet):
    #     '''
    #     Returns a suitable IP address for a controller node in the subnet.
    #     We prefer to use the second-to-last available IP address in the subnet (last is for the
    #     gateway). E.g. 172.30.0.0/24 -> 172.30.0.253
    #     '''
    #     all_ip_addresses = list(subnet.hosts())
    #     return all_ip_addresses[-2]

    def attempt_create_network(self, subnet_details):
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
        self.validate_name(subnet_details.name)

        # from docker.models.networks.create() help
        try:
            gateway_ip = subnet_details.gateway_ip()
            ipam_pool = docker.types.IPAMPool(subnet=str(subnet_details), gateway=gateway_ip)
            ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
            network = self.client.networks.create(subnet_details.name, driver='bridge',
                                                  ipam=ipam_config)
        except docker.errors.APIError as e:
            # network creation failed, assume that subnet was taken
            print(str(e))
            raise NetworkSubnetTaken

        return network

    def keep_attempting_to_create_network(self, name):
        '''
        Calls 'attempt_create_network' iteratively until a network is created, or until
        all possible subnets have been exhausted.

        Returns a tuple with the Docker network and the subnet (ipaddress object) that was used
        to create said network.

        If the name exists, NameExistsException is raised.
        If it is not possible to create a network (all IP ranges for the specified main network
        are taken) then NoNetworkSubnetsAvaialble is raised.
        '''

        network = None
        subnet_details = None
        possible_subnet_details = self.get_possible_subnet_details(name)

        while network is None:

            try:
                subnet_details = next(possible_subnet_details)
                network = self.attempt_create_network(subnet_details)
            except NetworkSubnetTaken:
                # will keep trying
                continue

            except StopIteration:
                # there are no more subnets to try
                msg = 'No more subnets available for network %s and CIDR bits %s'
                raise NoNetworkSubnetsAvaialble(msg % (str(self.supernet),
                                                       str(self.cidr_bits)))

        return (network, subnet_details)


class TestAttemptCreateNetwork(unittest.TestCase):

    def test_create_network_then_try_creating_it_again(self):

        supernet = '172.31.0.0/16'
        cidr_bits = 17
        create_network = CreateNetwork(supernet, cidr_bits)

        print('*** test_create_network_then_try_creating_it_again ***')
        print('This test will use the main network %s' % supernet)

        first_name = 'shouldbenew'
        sg = create_network.get_possible_subnet_details(first_name)
        first_subnet = next(sg)

        print('About to create Docker network: %s' % str(first_subnet))
        print('Make sure that this network does not exist in Docker!')

        input('Press Enter to continue')

        # create it, should not raise error because the network name and subnet are available
        create_network.validate_name(first_name)
        network = create_network.attempt_create_network(first_subnet)

        second_name = 'shouldalsobenew'
        first_subnet.name = second_name

        print('Created the first network, now try to create another one with same subnet')
        input('Expected error message: 403 Client Error: Forbidden \
("Pool overlaps with other one on this address space")')

        # create another network with the same subnet, now we should get an error
        with self.assertRaises(NetworkSubnetTaken):
            create_network.attempt_create_network(first_subnet)

        # try to clean up (remove first network)
        network.remove()
        print('Removed first network %s' % str(first_subnet))

    def test_keep_attempting_to_create_network(self):

        supernet = '172.31.0.0/16'
        cidr_bits = 17
        create_network = CreateNetwork(supernet, cidr_bits)

        print('*** test_keep_attempting_to_create_network ***')
        print('This test will use the main network %s and create two subnets' % supernet)
        print('Make sure there are no test networks in Docker!')
        input('Press Enter to continue')

        print('About to create first network, this should succeed')
        input('Press Enter to continue')
        (first_network, _) = create_network.keep_attempting_to_create_network('shouldbenew1')

        print('Created first network %s' % str(first_network))
        print('About to create second network, this should succeed')
        input('Press Enter to continue')

        (second_network, _) = create_network.keep_attempting_to_create_network('shouldbenew2')
        print('Created network %s' % str(second_network))

        print('About to try and create another network, this should fail')
        input('Press Enter to continue')

        with self.assertRaises(NoNetworkSubnetsAvaialble):
            create_network.keep_attempting_to_create_network('shouldbenew3')

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


class NetworkSubnetTaken(Exception):
    '''
    Expected to be raised when a network subnet is already taken by Docker.
    Should be used to indicate that another subnet is to be tried.
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
    # try to create a network
    unittest.main()
