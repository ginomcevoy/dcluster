'''
Unit tests for cluster.plan_basic
'''
import unittest

from dcluster.node import DefaultPlannedNode
from dcluster.cluster.planner import DefaultClusterPlan

from dcluster.tests.stubs import infra_stubs
from dcluster.tests.stubs import basic_stubs
from dcluster.tests.stubs import extended_stubs


class TestBuildSpecsOfDefaultClusterPlan(unittest.TestCase):
    '''
    Unit tests for cluster.planner.DefaultClusterPlan.build_specs()
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
        cluster_plan = basic_stubs.default_cluster_plan_stub(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'flavor': 'simple',
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': DefaultPlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos:7.7.1908-ssh',
                    ip_address='172.30.0.253',
                    role='head',
                    volumes=[],
                    static_text=''),
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            },
            'template': 'cluster-default.yml.j2',
            'volumes': []
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
        cluster_plan = basic_stubs.default_cluster_plan_stub(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'flavor': 'simple',
            'name': 'mycluster',
            'nodes': {
                '172.30.1.125': DefaultPlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos:7.7.1908-ssh',
                    ip_address='172.30.1.125',
                    role='head',
                    volumes=[],
                    static_text=''),
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.1.0/25',
                'gateway': 'gateway',
                'gateway_ip': '172.30.1.126'
            },
            'template': 'cluster-default.yml.j2',
            'volumes': []
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
        cluster_plan = basic_stubs.default_cluster_plan_stub(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'flavor': 'simple',
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': DefaultPlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos:7.7.1908-ssh',
                    ip_address='172.30.0.253',
                    role='head',
                    volumes=[],
                    static_text=''),
                '172.30.0.1': DefaultPlannedNode(
                    hostname='node001',
                    container='mycluster-node001',
                    image='centos:7.7.1908-ssh',
                    ip_address='172.30.0.1',
                    role='compute',
                    volumes=[],
                    static_text=''),
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            },
            'template': 'cluster-default.yml.j2',
            'volumes': []
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
        cluster_plan = basic_stubs.default_cluster_plan_stub(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'flavor': 'simple',
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': DefaultPlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos:7.7.1908-ssh',
                    ip_address='172.30.0.253',
                    role='head',
                    volumes=[],
                    static_text=''),
                '172.30.0.1': DefaultPlannedNode(
                    hostname='node001',
                    container='mycluster-node001',
                    image='centos:7.7.1908-ssh',
                    ip_address='172.30.0.1',
                    role='compute',
                    volumes=[],
                    static_text=''),
                '172.30.0.2': DefaultPlannedNode(
                    hostname='node002',
                    container='mycluster-node002',
                    image='centos:7.7.1908-ssh',
                    ip_address='172.30.0.2',
                    role='compute',
                    volumes=[],
                    static_text=''),
                '172.30.0.3': DefaultPlannedNode(
                    hostname='node003',
                    container='mycluster-node003',
                    image='centos:7.7.1908-ssh',
                    ip_address='172.30.0.3',
                    role='compute',
                    volumes=[],
                    static_text='')
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            },
            'template': 'cluster-default.yml.j2',
            'volumes': []
        }
        self.assertEqual(result, expected)

    def test_three_compute_nodes_extended(self):
        '''
        Cluster with three compute nodes using docker volumes
        '''
        # given
        cluster_name = 'mycluster'
        subnet_str = u'172.30.0.0/24'
        compute_count = 3
        cluster_plan = extended_stubs.basic_slurm_cluster_plan_stub(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'flavor': 'slurm',
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': DefaultPlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='rhel76-slurm:v2',
                    ip_address='172.30.0.253',
                    role='head',
                    volumes=[
                        '/home:/home',
                        '/opt/intel:/opt/intel',
                        '/srv/shared:/srv/dcluster/shared',
                        'var_lib_mysql:/var/lib/mysql',
                        'etc_munge:/etc/munge',
                        'etc_slurm:/etc/slurm',
                        'slurm_jobdir:/data',
                        'var_log_slurm:/var/log/slurm'
                    ],
                    static_text='''        command:
          - slurmctld
        environment:
          MYSQL_DATABASE: slurm_acct_db
          MYSQL_PASSWORD: password
          MYSQL_RANDOM_ROOT_PASSWORD: 'yes'
          MYSQL_USER: slurm
        expose:
          - '6817'
          - '6819'
      '''),
                '172.30.0.1': DefaultPlannedNode(
                    hostname='node001',
                    container='mycluster-node001',
                    image='rhel76-slurm:v2',
                    ip_address='172.30.0.1',
                    role='compute',
                    volumes=[
                        '/home:/home',
                        '/opt/intel:/opt/intel',
                        '/srv/shared:/srv/dcluster/shared',
                        'etc_munge:/etc/munge',
                        'etc_slurm:/etc/slurm',
                        'slurm_jobdir:/data',
                        'var_log_slurm:/var/log/slurm'
                    ],
                    static_text='''        command:
          - slurmd
        expose:
          - '6818'
        shm_size: 4g
      '''),
                '172.30.0.2': DefaultPlannedNode(
                    hostname='node002',
                    container='mycluster-node002',
                    image='rhel76-slurm:v2',
                    ip_address='172.30.0.2',
                    role='compute',
                    volumes=[
                        '/home:/home',
                        '/opt/intel:/opt/intel',
                        '/srv/shared:/srv/dcluster/shared',
                        'etc_munge:/etc/munge',
                        'etc_slurm:/etc/slurm',
                        'slurm_jobdir:/data',
                        'var_log_slurm:/var/log/slurm'
                    ],
                    static_text='''        command:
          - slurmd
        expose:
          - '6818'
        shm_size: 4g
      '''),
                '172.30.0.3': DefaultPlannedNode(
                    hostname='node003',
                    container='mycluster-node003',
                    image='rhel76-slurm:v2',
                    ip_address='172.30.0.3',
                    role='compute',
                    volumes=[
                        '/home:/home',
                        '/opt/intel:/opt/intel',
                        '/srv/shared:/srv/dcluster/shared',
                        'etc_munge:/etc/munge',
                        'etc_slurm:/etc/slurm',
                        'slurm_jobdir:/data',
                        'var_log_slurm:/var/log/slurm'
                    ],
                    static_text='''        command:
          - slurmd
        expose:
          - '6818'
        shm_size: 4g
      ''')
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            },
            'template': 'cluster-default.yml.j2',
            'volumes': [
                'var_lib_mysql',
                'etc_munge',
                'etc_slurm',
                'slurm_jobdir',
                'var_log_slurm'
            ]
        }
        self.assertEqual(result, expected)


class TestCreateDefaultClusterPlan(unittest.TestCase):
    '''
    Unit tests for cluster.planner.DefaultClusterPlan.create()
    '''

    def test_create(self):
        # given
        creation_request = basic_stubs.default_request_stub('test', 2)
        simple_config = basic_stubs.simple_config()
        cluster_network = infra_stubs.network_stub('test', u'172.30.0.0/24')

        # when
        cluster_plan = DefaultClusterPlan.create(creation_request, simple_config, cluster_network)

        # then
        result = cluster_plan.as_dict()
        expected = {
            'name': 'test',
            'head': {
                'hostname': 'head',
                'image': 'centos:7.7.1908-ssh'
            },
            'compute': {
                'hostname': {
                    'prefix': 'node',
                    'suffix_len': 3
                },
                'image': 'centos:7.7.1908-ssh'
            },
            'network': cluster_network.as_dict(),
            'template': 'cluster-default.yml.j2'
        }

        print(result)
        self.assertEqual(result, expected)