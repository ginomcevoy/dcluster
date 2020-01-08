import unittest
from collections import OrderedDict

from . import extended_stubs as stubs


class CreateExtendedHeadPlan(unittest.TestCase):
    '''
    Unit test for plan.extended.ExtendedNodePlanner.create_head_plan
    '''

    def setUp(self):
        self.maxDiff = None

    def test_create_head_plan(self):
        # given
        cluster_name = 'mycluster'
        subnet_str = u'172.30.0.0/24'
        compute_count = 3
        plan_data = stubs.slurm_plan_data_stub(cluster_name, compute_count)

        # under test
        node_planner = stubs.extended_node_planner_stub(cluster_name, subnet_str)

        # when
        result = node_planner.create_head_plan(plan_data)

        # then
        expected = {
            'hostname': 'head',
            'container': 'mycluster-head',
            'image': 'centos7:slurmctld',
            'ip_address': '172.30.0.253',
            'role': 'head',
            'static_text': '''        environment:
          MYSQL_DATABASE: slurm_acct_db
          MYSQL_PASSWORD: password
          MYSQL_RANDOM_ROOT_PASSWORD: 'yes'
          MYSQL_USER: slurm
        expose:
          - '6817'
          - '6819'
      ''',
            'volumes': [
                '/home:/home',
                '/opt/intel:/opt/intel',
                '/srv/shared:/srv/dcluster/shared',
                'var_lib_mysql:/var/lib/mysql',
                'etc_munge:/etc/munge',
                'etc_slurm:/etc/slurm',
                'slurm_jobdir:/data',
                'var_log_slurm:/var/log/slurm'
            ]
        }
        self.assertEqual(dict(result._asdict()), expected)