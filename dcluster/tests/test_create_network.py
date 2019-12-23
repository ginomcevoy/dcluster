import random
import string
import unittest


from dcluster import connect, create_network


DEFAULT_DOCKER_NETWORK = 'bridge'


class TestValidateNameIsAvailable(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = connect.client()

    def test_existing_name(self):
        with self.assertRaises(create_network.NameExistsException):
            # this network should be present (docker default)
            create_network.validate_name_is_available(DEFAULT_DOCKER_NETWORK, self.client)

    def test_new_name(self):
        # create a random string for name, extremely low chance of this existing...
        letters = string.ascii_lowercase
        random_name = ''.join(random.choice(letters) for i in range(8))

        # this should return the valid name
        result = create_network.validate_name_is_available(random_name, self.client)
        self.assertEqual(result, random_name)


class TestSubnetGenerator(unittest.TestCase):

    def test_four_subnets(self):
        gen = create_network.subnet_generator('172.30.0.0/16', 18)
        all_four_subnet_names = [str(subnet) for subnet in gen]

        expected = [
            '172.30.0.0/18',
            '172.30.64.0/18',
            '172.30.128.0/18',
            '172.30.192.0/18'
        ]
        self.assertEqual(all_four_subnet_names, expected)


class TestAttemptCreateNetwork(unittest.TestCase):
    pass
