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


def validate_name_is_available(name, client=None):
    '''
    Checks if a network name is available in Docker networks.

    Raises ValueError if name is not available (currently in use)
    Returns the name if it is available, without creating the network.
    '''

    if not client:
        client = connect.client()

    used_names = [network.name for network in client.networks.list()]
    if name in used_names:
        raise NameExistsException('Network name is already in use: %s' % name)

    # name is available, return it to be nice
    return name


def subnet_generator(main_network=MAIN_NETWORK, cidr_bits=CIDR_BITS):
    '''
    Create a generator for all subnets in the main network that have the specified prefix.
    '''
    # https://docs.python.org/3/library/ipaddress.html
    main_network = ipaddress.ip_network(main_network)
    possible_subnets = main_network.subnets(new_prefix=cidr_bits)
    return possible_subnets


def attempt_create_network(name, subnet, client=None):
    '''
    Tries to create a named network.

    If the name exists, NameExistsException is raised.
    If the name is (apparently) available but the network creation fails,
    NetworkSubnetTaken is raised.

    Subject to race conditions in the name query, but since we try multiple times this should not
    be a major issue.
    '''
    if not client:
        client = connect.client()

    # validate name to have one less reason that network creation fails
    validate_name_is_available(name, client)

    # from docker.models.networks.create() help
    try:
        ipam_pool = docker.types.IPAMPool(subnet=str(subnet))
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
        network = client.networks.create(name, driver='bridge', ipam=ipam_config)
    except docker.errors.APIError as e:
        # network creation failed, assume that subnet was taken
        print(str(e))
        raise NetworkSubnetTaken

    return network


def keep_attempting_to_create_network(name, main_network=MAIN_NETWORK, cidr_bits=CIDR_BITS,
                                      client=None):
    '''
    Calls 'attempt_create_network' iteratively until a network is created, or until
    all possible subnets have been exhausted.
    '''

    network = None
    possible_subnets = subnet_generator(main_network, cidr_bits)

    while network is None:

        try:
            subnet = next(possible_subnets)
            network = attempt_create_network(name, subnet, client)
        except NetworkSubnetTaken:
            # will keep trying
            continue

        except StopIteration:
            # there are no more subnets to try
            msg = 'No more subnets available for network %s and CIDR bits %s'
            raise NoNetworkSubnetsAvaialble(msg % (str(main_network), str(cidr_bits)))

    return network


class ClusterNetwork:
    pass


class TestAttemptCreateNetwork(unittest.TestCase):

    def test_create_network_then_try_creating_it_again(self):

        client = connect.client()

        main_network = '172.31.0.0/16'
        cidr_bits = 17

        sg = subnet_generator(main_network, cidr_bits)
        possible_subnet = next(sg)

        print('*** test_create_network_then_try_creating_it_again ***')
        print('This test will use the main network %s' % main_network)
        print('About to create Docker network: %s' % str(possible_subnet))
        print('Make sure that this network does not exist in Docker!')

        input('Press Enter to continue')

        # create it, should not raise error because the network name and subnet are available
        first_name = 'shouldbenew'
        second_name = 'shouldalsobenew'
        validate_name_is_available(first_name, client)
        network = attempt_create_network(first_name, possible_subnet, client)

        print('Created the first network, now try to create another one')
        input('Expected error message: 403 Client Error: Forbidden \
("Pool overlaps with other one on this address space")')

        # create another network with the same subnet, now we should get an error
        with self.assertRaises(NetworkSubnetTaken):
            attempt_create_network(second_name, possible_subnet, client)

        # try to clean up (remove first network)
        network.remove()
        print('Removed first network %s' % str(possible_subnet))

    def test_keep_attempting_to_create_network(self):

        main_network = '172.31.0.0/16'
        cidr_bits = 17

        print('*** test_keep_attempting_to_create_network ***')
        print('This test will use the main network %s and create two subnets' % main_network)
        print('Make sure there are no test networks in Docker!')
        input('Press Enter to continue')

        client = connect.client()

        print('About to create first network, this should succeed')
        input('Press Enter to continue')
        first_network = keep_attempting_to_create_network('shouldbenew1', main_network,
                                                          cidr_bits, client=client)

        print('Created first network %s' % str(first_network))
        print('About to create second network, this should succeed')
        input('Press Enter to continue')

        second_network = keep_attempting_to_create_network('shouldbenew2', main_network,
                                                           cidr_bits, client=client)
        print('Created network %s' % str(second_network))

        print('About to try and create another network, this should fail')
        input('Press Enter to continue')

        with self.assertRaises(NoNetworkSubnetsAvaialble):
            keep_attempting_to_create_network('shouldbenew3', main_network,
                                              cidr_bits, client=client)

        # try to clean up
        print('Failed as expected, cleaning up...')
        first_network.remove()
        second_network.remove()


if __name__ == '__main__':
    # try to create a network
    unittest.main()
