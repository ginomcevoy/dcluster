'''
Unit tests for cluster.plan_basic
'''
import unittest

from dcluster.node import BasicPlannedNode
from dcluster.cluster.planner import BasicClusterPlan

from dcluster.tests.stubs import infra_stubs
from dcluster.tests.stubs import basic_stubs as stubs


class TestBasicBuildSpecs(unittest.TestCase):
    '''
    Unit tests for cluster.planner.BasicClusterPlan.build_specs()
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
        cluster_plan = stubs.basic_cluster_plan_stub(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'flavor': 'simple',
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': BasicPlannedNode(
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
            },
            'template': 'cluster-basic.yml.j2'
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
        cluster_plan = stubs.basic_cluster_plan_stub(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'flavor': 'simple',
            'name': 'mycluster',
            'nodes': {
                '172.30.1.125': BasicPlannedNode(
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
            },
            'template': 'cluster-basic.yml.j2'
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
        cluster_plan = stubs.basic_cluster_plan_stub(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'flavor': 'simple',
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': BasicPlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos7:ssh',
                    ip_address='172.30.0.253',
                    role='head'),
                '172.30.0.1': BasicPlannedNode(
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
            },
            'template': 'cluster-basic.yml.j2'
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
        cluster_plan = stubs.basic_cluster_plan_stub(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'flavor': 'simple',
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': BasicPlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos7:ssh',
                    ip_address='172.30.0.253',
                    role='head'),
                '172.30.0.1': BasicPlannedNode(
                    hostname='node001',
                    container='mycluster-node001',
                    image='centos7:ssh',
                    ip_address='172.30.0.1',
                    role='compute'),
                '172.30.0.2': BasicPlannedNode(
                    hostname='node002',
                    container='mycluster-node002',
                    image='centos7:ssh',
                    ip_address='172.30.0.2',
                    role='compute'),
                '172.30.0.3': BasicPlannedNode(
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
            },
            'template': 'cluster-basic.yml.j2'
        }
        self.assertEqual(result, expected)


class CreateBasicClusterPlanTest(unittest.TestCase):
    '''
    Unit tests for cluster.planner.BasicClusterPlan.create()
    '''

    def test_create(self):
        # given
        creation_request = stubs.basic_request_stub('test', 2)
        basic_config = stubs.basic_config()
        cluster_network = infra_stubs.network_stub('test', u'172.30.0.0/24')

        # when
        cluster_plan = BasicClusterPlan.create(creation_request, basic_config, cluster_network)

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
            'template': 'cluster-basic.yml.j2'
        }

        print(result)
        self.assertEqual(result, expected)
