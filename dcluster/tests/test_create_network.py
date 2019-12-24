import random
import string
import unittest


from dcluster import create_network


DEFAULT_DOCKER_NETWORK = 'bridge'


class TestValidateNameIsAvailable(unittest.TestCase):

    def setUp(self):
        self.creator = create_network.CreateNetwork()

    def test_existing_name(self):
        with self.assertRaises(create_network.NameExistsException):
            # this network should be present (docker default)
            self.creator.validate_name(DEFAULT_DOCKER_NETWORK)

    def test_new_name(self):
        # create a random string for name, extremely low chance of this existing...
        letters = string.ascii_lowercase
        random_name = ''.join(random.choice(letters) for i in range(8))

        # this should return the valid name
        result = self.creator.validate_name(random_name)
        self.assertEqual(result, random_name)


class TestSubnets(unittest.TestCase):

    def test_four_subnets(self):
        creator = create_network.CreateNetwork('172.30.0.0/16', 18)
        gen = creator.subnet_generator
        all_four_subnet_names = [str(subnet) for subnet in gen]

        expected = [
            '172.30.0.0/18',
            '172.30.64.0/18',
            '172.30.128.0/18',
            '172.30.192.0/18'
        ]
        self.assertEqual(all_four_subnet_names, expected)

    def test_gateway_for_24(self):
        creator = create_network.CreateNetwork('172.30.0.0/16', 24)
        gen = creator.subnet_generator
        first_network = next(gen)
        gateway = creator.gateway_ip(first_network)

        expected = '172.30.0.254'
        self.assertEqual(str(gateway), expected)

    def test_gateway_for_18(self):
        creator = create_network.CreateNetwork('172.30.0.0/16', 18)
        gen = creator.subnet_generator
        next(gen)
        second_network = next(gen)  # 172.30.64.0/18
        gateway = creator.gateway_ip(second_network)

        expected = '172.30.127.254'
        self.assertEqual(str(gateway), expected)

    def test_controller_for_24(self):
        creator = create_network.CreateNetwork('172.30.0.0/16', 24)
        gen = creator.subnet_generator
        first_network = next(gen)
        controller_ip = creator.controller_ip(first_network)

        expected = '172.30.0.253'
        self.assertEqual(str(controller_ip), expected)
