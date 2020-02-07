import unittest

from dcluster.plan import ExtendedPlannedNode
from . import extended_stubs as stubs


class TestExtendedBuildSpecs(unittest.TestCase):
    '''
    Unit tests for plan.simple.ExtendedClusterPlan.build_specs()
    '''

    def setUp(self):
        self.maxDiff = None

    def test_three_compute_nodes(self):
        '''
        Cluster with three compute nodes
        '''
        # given
        cluster_name = 'mycluster'
        subnet_str = u'172.30.0.0/24'
        compute_count = 3
        cluster_plan = stubs.slurm_cluster_plan_stub(cluster_name, subnet_str, compute_count)

        # when
        result = cluster_plan.build_specs()

        # then
        expected = {
            'flavor': 'slurm',
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': ExtendedPlannedNode(
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
                '172.30.0.1': ExtendedPlannedNode(
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
                '172.30.0.2': ExtendedPlannedNode(
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
                '172.30.0.3': ExtendedPlannedNode(
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
            'template': 'cluster-extended.yml.j2',
            'volumes': [
                'var_lib_mysql',
                'etc_munge',
                'etc_slurm',
                'slurm_jobdir',
                'var_log_slurm'
            ]
        }
        self.assertEqual(result, expected)
