import unittest

from dcluster.node import SimplePlannedNode

from . import simple_stubs as stubs


class CreateComputeHostname(unittest.TestCase):

    def setUp(self):
        cluster_name = 'test'
        subnet_str = u'172.30.0.0/24'
        compute_count = 3
        self.plan_data = stubs.simple_plan_data_stub(cluster_name, compute_count)
        self.node_planner = stubs.simple_node_planner_stub(cluster_name, subnet_str)

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


class CreateSimpleComputeNode(unittest.TestCase):

    def setUp(self):
        cluster_name = 'mycluster'
        subnet_str = u'172.30.0.0/24'
        compute_count = 3
        self.plan_data = stubs.simple_plan_data_stub(cluster_name, compute_count)
        self.node_planner = stubs.simple_node_planner_stub(cluster_name, subnet_str)

    def test_compute_index_1(self):
        # given
        index = 1

        # when
        result = self.node_planner.create_compute_plan(self.plan_data, index, '172.30.0.2')

        # then
        expected = SimplePlannedNode(hostname='node002',
                                     container='mycluster-node002',
                                     image='centos7:ssh',
                                     ip_address='172.30.0.2',
                                     role='compute')
        self.assertEqual(result, expected)
