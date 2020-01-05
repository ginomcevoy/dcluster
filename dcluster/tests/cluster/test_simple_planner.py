import ipaddress
import unittest

from dcluster.cluster import node
from dcluster.cluster import simple as simple_cluster
from dcluster.request import simple as simple_request

from dcluster import networking


class TestBuildSpecs(unittest.TestCase):
    '''
    Unit tests for cluster.simple.ClusterPlanner.build_specs
    '''

    def setUp(self):
        self.planner = simple_cluster.SimplePlanner()
        self.maxDiff = None

    def test_zero_compute_nodes(self):
        '''
        Cluster without compute nodes, just the head
        '''
        # given
        compute_nodes = 0
        cluster_specs_simple = self.create_simple_request('mycluster', compute_nodes)
        cluster_network = self.stub_network(u'172.30.0.0/24', cluster_specs_simple)

        # when
        result = self.planner.build_specs(cluster_specs_simple, cluster_network)

        # then
        expected = {
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': node.PlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos7:ssh',
                    ip_address='172.30.0.253',
                    role='head')
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            }
        }
        self.assertEqual(result, expected)

    def test_zero_compute_nodes_small_subnet(self):
        '''
        Cluster without compute nodes, just the head, small subnet
        '''
        # given
        compute_nodes = 0
        cluster_specs_simple = self.create_simple_request('mycluster', compute_nodes)
        cluster_network = self.stub_network(u'172.30.1.0/25', cluster_specs_simple)

        # when
        result = self.planner.build_specs(cluster_specs_simple, cluster_network)

        # then
        expected = {
            'name': 'mycluster',
            'nodes': {
                '172.30.1.125': node.PlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos7:ssh',
                    ip_address='172.30.1.125',
                    role='head')
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.1.0/25',
                'gateway': 'gateway',
                'gateway_ip': '172.30.1.126'
            }
        }
        self.assertEqual(result, expected)

    def test_one_compute_node(self):
        '''
        Cluster with one compute node
        '''
        # given
        compute_nodes = 1
        cluster_specs_simple = self.create_simple_request('mycluster', compute_nodes)
        cluster_network = self.stub_network(u'172.30.0.0/24', cluster_specs_simple)

        # when
        result = self.planner.build_specs(cluster_specs_simple, cluster_network)

        # then
        expected = {
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': node.PlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos7:ssh',
                    ip_address='172.30.0.253',
                    role='head'),
                '172.30.0.1': node.PlannedNode(
                    hostname='node001',
                    container='mycluster-node001',
                    image='centos7:ssh',
                    ip_address='172.30.0.1',
                    role='compute')
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            }
        }
        self.assertEqual(result, expected)

    def test_three_compute_nodes(self):
        '''
        Cluster with three compute nodes
        '''
        # given
        compute_nodes = 3
        cluster_specs_simple = self.create_simple_request('mycluster', compute_nodes)
        cluster_network = self.stub_network(u'172.30.0.0/24', cluster_specs_simple)

        # when
        result = self.planner.build_specs(cluster_specs_simple, cluster_network)

        # then
        expected = {
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': node.PlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos7:ssh',
                    ip_address='172.30.0.253',
                    role='head'),
                '172.30.0.1': node.PlannedNode(
                    hostname='node001',
                    container='mycluster-node001',
                    image='centos7:ssh',
                    ip_address='172.30.0.1',
                    role='compute'),
                '172.30.0.2': node.PlannedNode(
                    hostname='node002',
                    container='mycluster-node002',
                    image='centos7:ssh',
                    ip_address='172.30.0.2',
                    role='compute'),
                '172.30.0.3': node.PlannedNode(
                    hostname='node003',
                    container='mycluster-node003',
                    image='centos7:ssh',
                    ip_address='172.30.0.3',
                    role='compute')
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            }
        }
        self.assertEqual(result, expected)

    def create_simple_request(self, name, compute_count):
        return simple_request.ClusterRequestSimple(name, compute_count, 'simple')

    def stub_network(self, subnet_str, cluster_specs_simple):
        subnet = ipaddress.ip_network(subnet_str)
        return networking.ClusterNetwork(subnet, cluster_specs_simple.name)
