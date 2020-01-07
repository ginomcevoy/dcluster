'''
Unit tests for plan.simple
'''

import ipaddress
import unittest
from collections import OrderedDict

from dcluster import config, networking

from dcluster.plan import SimplePlannedNode, SimpleCreationRequest
from dcluster.plan.simple import SimpleClusterPlan, SimpleNodePlanner, simple_plan_data


def simple_request_stub(cluster_name, compute_count):
    return SimpleCreationRequest(cluster_name, compute_count, 'simple')


def network_stub(subnet_str, cluster_name):
    subnet = ipaddress.ip_network(subnet_str)
    return networking.ClusterNetwork(subnet, cluster_name)


def simple_plan_data_stub(cluster_name, compute_count):
    simple_config = config.for_cluster('simple')
    request = simple_request_stub(cluster_name, compute_count)
    return simple_plan_data(simple_config, request)


def simple_node_planner_stub(cluster_name, subnet_str):
    network = network_stub(subnet_str, cluster_name)
    return SimpleNodePlanner(network)


def simple_cluster_plan_stub(cluster_name='test', subnet_str=u'172.30.0.0/24', compute_count=3):
    creation_request = simple_request_stub(cluster_name, compute_count)
    cluster_network = network_stub(subnet_str, cluster_name)
    simple_config = config.for_cluster('simple')

    return SimpleClusterPlan.create(creation_request, simple_config, cluster_network)


class CreateComputeHostname(unittest.TestCase):

    def setUp(self):
        cluster_name = 'test'
        subnet_str = u'172.30.0.0/24'
        compute_count = 3
        self.plan_data = simple_plan_data_stub(cluster_name, compute_count)
        self.node_planner = simple_node_planner_stub(cluster_name, subnet_str)

    def test_hostname_0(self):
        # given
        index = 0

        # when
        result = self.node_planner.create_compute_hostname(self.plan_data, index)

        # then
        self.assertEqual(result, 'node001')

    def test_hostname_10(self):
        # given
        index = 10

        # when
        result = self.node_planner.create_compute_hostname(self.plan_data, index)

        # then
        self.assertEqual(result, 'node011')


class TestSimpleBuildSpecs(unittest.TestCase):
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
        cluster_plan = simple_cluster_plan_stub(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'flavor': 'simple',
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': SimplePlannedNode(
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
            'template': 'cluster-simple.yml.j2'
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
        cluster_plan = simple_cluster_plan_stub(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'flavor': 'simple',
            'name': 'mycluster',
            'nodes': {
                '172.30.1.125': SimplePlannedNode(
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
            'template': 'cluster-simple.yml.j2'
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
        cluster_plan = simple_cluster_plan_stub(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'flavor': 'simple',
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': SimplePlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos7:ssh',
                    ip_address='172.30.0.253',
                    role='head'),
                '172.30.0.1': SimplePlannedNode(
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
            'template': 'cluster-simple.yml.j2'
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
        cluster_plan = simple_cluster_plan_stub(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'flavor': 'simple',
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': SimplePlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos7:ssh',
                    ip_address='172.30.0.253',
                    role='head'),
                '172.30.0.1': SimplePlannedNode(
                    hostname='node001',
                    container='mycluster-node001',
                    image='centos7:ssh',
                    ip_address='172.30.0.1',
                    role='compute'),
                '172.30.0.2': SimplePlannedNode(
                    hostname='node002',
                    container='mycluster-node002',
                    image='centos7:ssh',
                    ip_address='172.30.0.2',
                    role='compute'),
                '172.30.0.3': SimplePlannedNode(
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
            'template': 'cluster-simple.yml.j2'
        }
        self.assertEqual(result, expected)


class CreateSimpleClusterPlanTest(unittest.TestCase):
    '''
    Unit tests for plan.simple.SimpleClusterPlan.create()
    '''

    def test_create(self):
        # given
        creation_request = simple_request_stub('test', 2)
        simple_config = config.for_cluster('simple')
        cluster_network = network_stub(u'172.30.0.0/24', 'test')

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

        print(result)
        self.assertEqual(result, expected)


class ExtendedBuildSpecs(unittest.TestCase):
    '''
    Unit tests for plan.extended.ExtendedClusterPlan.build_specs()
    '''

    def setUp(self):
        self.maxDiff = None

    def a_test_two_compute_nodes_slurm(self):
        '''
        Slurm cluster with two compute nodes
        '''
        # given
        cluster_name = 'mycluster'
        subnet_str = u'172.30.0.0/24'
        compute_count = 2
        cluster_plan = simple_cluster_plan_stub(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'flavor': 'slurm',
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': {
                    'hostname': 'head',
                    'container': 'mycluster-head',
                    'image': 'centos7:ssh',
                    'ip_address': '172.30.0.253',
                    'role': 'head',
                    'volumes': [
                        '/home:/home',
                        '/opt/intel:/opt/intel',
                        '/srv/shared:/srv/dcluster/shared',
                        'var_lib_mysql:/var/lib/mysql',
                        'etc_munge:/etc/munge',
                        'etc_slurm:/etc/slurm',
                        'slurm_jobdir:/data',
                        'var_log_slurm:/var/log/slurm'
                    ],
                    'static_text': '''        environment:
            MYSQL_RANDOM_ROOT_PASSWORD: "yes"
            MYSQL_DATABASE: slurm_acct_db
            MYSQL_USER: slurm
            MYSQL_PASSWORD: password
        expose:
            - '6817'
            - \'6819\''''
                },
                '172.30.0.1': {
                    'hostname': 'node001',
                    'container': 'mycluster-node001',
                    'image': 'centos7:ssh',
                    'ip_address': '172.30.0.1',
                    'role': 'compute',
                    'volumes': [
                        '/home:/home',
                        '/opt/intel:/opt/intel',
                        '/srv/shared:/srv/dcluster/shared',
                        'etc_munge:/etc/munge',
                        'etc_slurm:/etc/slurm',
                        'slurm_jobdir:/data',
                        'var_log_slurm:/var/log/slurm'
                    ],
                    'static_text': '''        expose:
            - '6818'
        shm_size: 4g'''
                },
                '172.30.0.2': {
                    'hostname': 'node002',
                    'container': 'mycluster-node002',
                    'image': 'centos7:ssh',
                    'ip_address': '172.30.0.2',
                    'role': 'compute',
                    'volumes': [
                        '/home:/home',
                        '/opt/intel:/opt/intel',
                        '/srv/shared:/srv/dcluster/shared',
                        'etc_munge:/etc/munge',
                        'etc_slurm:/etc/slurm',
                        'slurm_jobdir:/data',
                        'var_log_slurm:/var/log/slurm'
                    ],
                    'static_text': '''        expose:
            - '6818'
        shm_size: 4g'''
                }
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            },
            'volumes': [
                'etc_munge',
                'etc_slurm',
                'slurm_jobdir',
                'var_lib_mysql',
                'var_log_slurm'
            ],
        }
        self.assertEquals(result, expected)
