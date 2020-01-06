'''
Unit tests for plan.simple
'''

import ipaddress
import unittest

from dcluster import config, networking

from dcluster.plan import PlannedNode, SimpleCreationRequest
from dcluster.plan.simple import SimpleClusterPlan


def stub_simple_request(cluster_name, compute_count):
    return SimpleCreationRequest(cluster_name, compute_count, 'simple')


def stub_network(subnet_str, cluster_name):
    subnet = ipaddress.ip_network(subnet_str)
    return networking.ClusterNetwork(subnet, cluster_name)


def stub_cluster_plan(cluster_name='test', subnet_str=u'172.30.0.0/24', compute_count=3):
    creation_request = stub_simple_request(cluster_name, compute_count)
    cluster_network = stub_network(subnet_str, cluster_name)
    simple_config = config.for_cluster('simple')

    return SimpleClusterPlan.create(creation_request, simple_config, cluster_network)


class CreateSimpleClusterPlanTest(unittest.TestCase):
    '''
    Unit tests for plan.simple.SimpleClusterPlan.create()
    '''

    def test_create(self):
        # given
        creation_request = stub_simple_request('test', 2)
        simple_config = config.for_cluster('simple')
        cluster_network = stub_network(u'172.30.0.0/24', 'test')

        # when
        cluster_plan = SimpleClusterPlan.create(creation_request, simple_config, cluster_network)

        # then
        result = cluster_plan.as_dict()
        expected = {
            'name': 'test',
            'head': {
                'hostname': 'head',
                'image': 'centos7:ssh'
            },
            'compute': {
                'hostname': {
                    'prefix': 'node',
                    'suffix_len': 3
                },
                'image': 'centos7:ssh'
            },
            'network': cluster_network.as_dict(),
            'template': 'cluster-simple.yml.j2'
        }

        self.assertEqual(result, expected)


class CreateComputeHostname(unittest.TestCase):

    def setUp(self):
        cluster_name = 'test'
        subnet_str = u'172.30.0.0/24'
        compute_count = 3
        self.cluster_plan = stub_cluster_plan(cluster_name, subnet_str, compute_count)

    def test_hostname_0(self):
        # given
        index = 0

        # when
        result = self.cluster_plan.create_compute_hostname(index)

        # then
        self.assertEqual(result, 'node001')

    def test_hostname_10(self):
        # given
        index = 10

        # when
        result = self.cluster_plan.create_compute_hostname(index)

        # then
        self.assertEqual(result, 'node011')


class TestBuildSpecs(unittest.TestCase):
    '''
    Unit tests for plan.simple.SimpleClusterPlan.build_specs()
    '''

    def setUp(self):
        self.maxDiff = None

    def test_zero_compute_nodes(self):
        '''
        Cluster without compute nodes, just the head
        '''
        # given
        cluster_name = 'mycluster'
        subnet_str = u'172.30.0.0/24'
        compute_count = 0
        cluster_plan = stub_cluster_plan(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': PlannedNode(
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
        cluster_name = 'mycluster'
        subnet_str = u'172.30.1.0/25'
        compute_count = 0
        cluster_plan = stub_cluster_plan(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'name': 'mycluster',
            'nodes': {
                '172.30.1.125': PlannedNode(
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
        cluster_name = 'mycluster'
        subnet_str = u'172.30.0.0/24'
        compute_count = 1
        cluster_plan = stub_cluster_plan(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': PlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos7:ssh',
                    ip_address='172.30.0.253',
                    role='head'),
                '172.30.0.1': PlannedNode(
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
        cluster_name = 'mycluster'
        subnet_str = u'172.30.0.0/24'
        compute_count = 3
        cluster_plan = stub_cluster_plan(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': PlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos7:ssh',
                    ip_address='172.30.0.253',
                    role='head'),
                '172.30.0.1': PlannedNode(
                    hostname='node001',
                    container='mycluster-node001',
                    image='centos7:ssh',
                    ip_address='172.30.0.1',
                    role='compute'),
                '172.30.0.2': PlannedNode(
                    hostname='node002',
                    container='mycluster-node002',
                    image='centos7:ssh',
                    ip_address='172.30.0.2',
                    role='compute'),
                '172.30.0.3': PlannedNode(
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
