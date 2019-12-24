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

from . import MAIN_NETWORK, CIDR_BITS
from . import connect


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


class CreateNetwork:

    def __init__(self, main_network=MAIN_NETWORK, cidr_bits=CIDR_BITS, client=None):
        if not client:
            client = connect.client()

        self.client = client
        self.main_network = main_network
        self.cidr_bits = cidr_bits

    def validate_name(self, name):
        used_names = [network.name for network in self.client.networks.list()]
        if name in used_names:
            raise NameExistsException('Network name is already in use: %s' % name)

        # name is available, return it to be nice
        return name

    @property
    def subnet_generator(self):
        '''
        Generator for all subnets in the main network that have the specified prefix.
        '''
        # https://docs.python.org/3/library/ipaddress.html
        network = ipaddress.ip_network(self.main_network)
        possible_subnets = network.subnets(new_prefix=self.cidr_bits)
        return possible_subnets

    def gateway_ip(self, subnet):
        '''
        Returns a suitable gateway IP address for a subnet. We prefer to use the last available IP
        address in the subnet. E.g. 172.30.0.0/24 -> 172.30.0.254
        '''
        all_ip_addresses = list(subnet.hosts())
        return all_ip_addresses[-1]

    def controller_ip(self, subnet):
        '''
        Returns a suitable IP address for a controller node in the subnet.
        We prefer to use the second-to-last available IP address in the subnet (last is for the
        gateway). E.g. 172.30.0.0/24 -> 172.30.0.253
        '''
        all_ip_addresses = list(subnet.hosts())
        return all_ip_addresses[-2]

    def attempt_create_network(self, name, subnet):
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
        self.validate_name(name)

        # from docker.models.networks.create() help
        try:
            gateway = self.gateway_ip(subnet)
            ipam_pool = docker.types.IPAMPool(subnet=str(subnet), gateway=str(gateway))
            ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
            network = self.client.networks.create(name, driver='bridge', ipam=ipam_config)
        except docker.errors.APIError as e:
            # network creation failed, assume that subnet was taken
            print(str(e))
            raise NetworkSubnetTaken

        return (network, subnet)

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
        possible_subnets = self.subnet_generator

        while network is None:

            try:
                subnet = next(possible_subnets)
                (network, subnet) = self.attempt_create_network(name, subnet)
            except NetworkSubnetTaken:
                # will keep trying
                continue

            except StopIteration:
                # there are no more subnets to try
                msg = 'No more subnets available for network %s and CIDR bits %s'
                raise NoNetworkSubnetsAvaialble(msg % (str(self.main_network),
                                                       str(self.cidr_bits)))

        return (network, subnet)


class TestAttemptCreateNetwork(unittest.TestCase):

    def test_create_network_then_try_creating_it_again(self):

        main_network = '172.31.0.0/16'
        cidr_bits = 17
        create_network = CreateNetwork(main_network, cidr_bits)

        sg = create_network.subnet_generator
        possible_subnet = next(sg)

        print('*** test_create_network_then_try_creating_it_again ***')
        print('This test will use the main network %s' % main_network)
        print('About to create Docker network: %s' % str(possible_subnet))
        print('Make sure that this network does not exist in Docker!')

        input('Press Enter to continue')

        # create it, should not raise error because the network name and subnet are available
        first_name = 'shouldbenew'
        second_name = 'shouldalsobenew'
        create_network.validate_name(first_name)
        network = create_network.attempt_create_network(first_name, possible_subnet)

        print('Created the first network, now try to create another one')
        input('Expected error message: 403 Client Error: Forbidden \
("Pool overlaps with other one on this address space")')

        # create another network with the same subnet, now we should get an error
        with self.assertRaises(NetworkSubnetTaken):
            create_network.attempt_create_network(second_name, possible_subnet)

        # try to clean up (remove first network)
        network.remove()
        print('Removed first network %s' % str(possible_subnet))

    def test_keep_attempting_to_create_network(self):

        main_network = '172.31.0.0/16'
        cidr_bits = 17
        create_network = CreateNetwork(main_network, cidr_bits)

        print('*** test_keep_attempting_to_create_network ***')
        print('This test will use the main network %s and create two subnets' % main_network)
        print('Make sure there are no test networks in Docker!')
        input('Press Enter to continue')

        print('About to create first network, this should succeed')
        input('Press Enter to continue')
        first_network = create_network.keep_attempting_to_create_network('shouldbenew1')

        print('Created first network %s' % str(first_network))
        print('About to create second network, this should succeed')
        input('Press Enter to continue')

        second_network = create_network.keep_attempting_to_create_network('shouldbenew2')
        print('Created network %s' % str(second_network))

        print('About to try and create another network, this should fail')
        input('Press Enter to continue')

        with self.assertRaises(NoNetworkSubnetsAvaialble):
            create_network.keep_attempting_to_create_network('shouldbenew3')

        # try to clean up
        print('Failed as expected, cleaning up...')
        first_network.remove()
        second_network.remove()


if __name__ == '__main__':
    # try to create a network
    unittest.main()
