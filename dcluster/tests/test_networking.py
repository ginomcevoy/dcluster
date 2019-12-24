import random
import string
import unittest


from dcluster import networking


DEFAULT_DOCKER_NETWORK = 'bridge'


class TestSubnetDetails(unittest.TestCase):

    def test_gateway_for_24(self):
        network_addresses = networking.SubnetDetails.from_first_subnet('172.30.0.0/16', 24)
        gateway = network_addresses.gateway_ip()

        expected = '172.30.0.254'
        self.assertEqual(gateway, expected)

    def test_gateway_for_25(self):
        network_addresses = networking.SubnetDetails.from_first_subnet('172.30.0.0/16', 25)
        gateway = network_addresses.gateway_ip()

        expected = '172.30.0.126'
        self.assertEqual(gateway, expected)

    def test_controller_for_24(self):
        network_addresses = networking.SubnetDetails.from_first_subnet('172.30.0.0/16', 24)
        controller_ip = network_addresses.controller_ip()

        expected = '172.30.0.253'
        self.assertEqual(controller_ip, expected)

    def test_request_three_compute_nodes_ok(self):
        network_addresses = networking.SubnetDetails.from_first_subnet('172.30.0.0/16', 24)
        compute_ips = network_addresses.compute_ips(3)

        expected = [
            '172.30.0.1',
            '172.30.0.2',
            '172.30.0.3'
        ]
        self.assertEqual(compute_ips, expected)

    def test_request_three_compute_nodes_subnet_too_small(self):
        # this small subnet only has 4 available IP addresses, and we need two for gateway
        # and controller
        network_addresses = networking.SubnetDetails.from_first_subnet('172.30.0.0/16', 30)

        with self.assertRaises(networking.NetworkSubnetTooSmall):
            network_addresses.compute_ips(3)

    def test_four_subnets(self):
        generator = networking.SubnetDetails.subnet_details_generator('172.30.0.0/16', 18)
        all_four_subnet_names = [str(subnet_details) for subnet_details in generator]

        expected = [
            '172.30.0.0/18',
            '172.30.64.0/18',
            '172.30.128.0/18',
            '172.30.192.0/18'
        ]
        self.assertEqual(all_four_subnet_names, expected)


class TestValidateNameIsAvailable(unittest.TestCase):

    def setUp(self):
        self.creator = networking.CreateNetwork()

    def test_existing_name(self):
        with self.assertRaises(networking.NameExistsException):
            # this network should be present (docker default)
            self.creator.validate_name(DEFAULT_DOCKER_NETWORK)

    def test_new_name(self):
        # create a random string for name, extremely low chance of this existing...
        letters = string.ascii_lowercase
        random_name = ''.join(random.choice(letters) for i in range(8))

        # this should return the valid name
        result = self.creator.validate_name(random_name)
        self.assertEqual(result, random_name)
