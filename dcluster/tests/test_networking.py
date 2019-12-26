import ipaddress
import random
import string
import unittest


from dcluster import networking


DEFAULT_DOCKER_NETWORK = 'bridge'


class TestClusterNetwork(unittest.TestCase):

    def test_gateway_for_24(self):
        cluster_network = self.create_network('172.30.0.0/16', 24, 'test')
        gateway = cluster_network.gateway_ip()

        expected = '172.30.0.254'
        self.assertEqual(gateway, expected)

    def test_gateway_for_25(self):
        cluster_network = self.create_network('172.30.0.0/16', 25, 'test')
        gateway = cluster_network.gateway_ip()

        expected = '172.30.0.126'
        self.assertEqual(gateway, expected)

    def test_head_for_24(self):
        cluster_network = self.create_network('172.30.0.0/16', 24, 'test')
        head_ip = cluster_network.head_ip()

        expected = '172.30.0.253'
        self.assertEqual(head_ip, expected)

    def test_request_three_compute_nodes_ok(self):
        cluster_network = self.create_network('172.30.0.0/16', 24, 'test')
        compute_ips = cluster_network.compute_ips(3)

        expected = [
            '172.30.0.1',
            '172.30.0.2',
            '172.30.0.3'
        ]
        self.assertEqual(compute_ips, expected)

    def test_request_three_compute_nodes_subnet_too_small(self):
        # this small subnet only has 4 available IP addresses,
        # and we need two for gateway and head
        cluster_network = self.create_network('172.30.0.0/16', 30, 'test')

        with self.assertRaises(networking.NetworkSubnetTooSmall):
            cluster_network.compute_ips(3)

    def test_four_subnets(self):
        generator = networking.ClusterNetwork.generator('172.30.0.0/16', 18, 'test')
        all_four_subnet_names = [str(cluster_network) for cluster_network in generator]

        expected = [
            '172.30.0.0/18',
            '172.30.64.0/18',
            '172.30.128.0/18',
            '172.30.192.0/18'
        ]
        self.assertEqual(all_four_subnet_names, expected)

    def create_network(self, supernet, cidr_bits, name):
        return networking.ClusterNetwork.from_first_subnet(supernet, cidr_bits, name)


class TestBuildHostDetails(unittest.TestCase):

    def test_zero_compute_nodes(self):
        # given
        network = self.create_stub_docker_cluster_network('172.30.0.0/24', 'mycluster')
        compute_nodes = 0

        # when
        result = network.build_host_details(compute_nodes)

        # then
        expected = {
            '172.30.0.253': {
                'hostname': 'slurmctld',
                'container': 'mycluster-slurmctld',
                'type': 'head'
            }
        }
        self.assertEqual(result, expected)

    def test_zero_compute_nodes2(self):
        # given
        network = self.create_stub_docker_cluster_network('172.30.1.0/24', 'mycluster')
        compute_nodes = 0

        # when
        result = network.build_host_details(compute_nodes)

        # then
        expected = {
            '172.30.1.253': {
                'hostname': 'slurmctld',
                'container': 'mycluster-slurmctld',
                'type': 'head'
            }
        }
        self.assertEqual(result, expected)

    def test_one_compute_node(self):
        # given
        network = self.create_stub_docker_cluster_network('172.30.0.0/24', 'mycluster')
        compute_nodes = 1

        # when
        result = network.build_host_details(compute_nodes)

        # then
        expected = {
            '172.30.0.253': {
                'hostname': 'slurmctld',
                'container': 'mycluster-slurmctld',
                'type': 'head'
            },
            '172.30.0.1': {
                'hostname': 'node001',
                'container': 'mycluster-node001',
                'type': 'compute'
            }
        }
        self.assertEqual(result, expected)

    def test_three_compute_nodes(self):
        # given
        network = self.create_stub_docker_cluster_network('172.30.0.0/24', 'mycluster')
        compute_nodes = 3

        # when
        result = network.build_host_details(compute_nodes)

        # then
        expected = {
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
        }
        self.assertEqual(result, expected)

    def create_stub_docker_cluster_network(self, subnet_str, cluster_name):
        subnet = ipaddress.ip_network(subnet_str)
        return networking.DockerClusterNetwork.from_subnet_and_name(subnet, cluster_name, None)


class TestValidateNameIsAvailable(unittest.TestCase):

    def setUp(self):
        self.creator = networking.DockerClusterNetworkFactory()

    def test_existing_name(self):
        with self.assertRaises(networking.NameExistsException):
            # this network should be present (docker default)
            self.creator.validate_network_name(DEFAULT_DOCKER_NETWORK)

    def test_new_name(self):
        # create a random string for name, extremely low chance of this existing...
        letters = string.ascii_lowercase
        random_name = ''.join(random.choice(letters) for i in range(8))

        # this should return the valid name
        result = self.creator.validate_network_name(random_name)
        self.assertEqual(result, random_name)
