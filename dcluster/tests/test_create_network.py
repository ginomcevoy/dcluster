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


class TestSubnetGenerator(unittest.TestCase):

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
