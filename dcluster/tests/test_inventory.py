import unittest
import yaml

from dcluster import ALL, CHILDREN, HOSTS
from dcluster import inventory

from . import test_resources


class TestCreateAnsibleInventory(unittest.TestCase):

    def setUp(self):
        resources = test_resources.TestResources()
        network_name = 'example'
        self.inventory = inventory.AnsibleInventory(network_name, self.host_details())
        self.expected = resources.expected_cluster_inventory
        self.maxDiff = None

    def test_hosts(self):
        created = self.inventory.create_dict()
        self.assertEqual(created[ALL][HOSTS], self.expected[ALL][HOSTS])

    def test_head_present(self):
        created = self.inventory.create_dict()

        self.assertTrue(CHILDREN in created[ALL].keys())
        self.assertTrue('head' in created[ALL][CHILDREN].keys())

    def test_head_contents(self):
        created = self.inventory.create_dict()

        self.assertEqual(created[ALL][CHILDREN]['head'],
                         self.expected[ALL][CHILDREN]['head'])

    def test_complete_output(self):
        created = self.inventory.create_dict()
        self.assertEqual(created, self.expected)

    def test_yaml_output(self):
        output_filename = '/tmp/dcluster_output_cluster.yml'
        self.inventory.to_yaml(output_filename)

        with open(output_filename, 'r') as of:
            actual_output = yaml.load(of)

        self.assertEqual(actual_output, self.expected)

    def host_details(self):
        host_details = {
            '172.30.0.253': {'hostname': 'slurmctld', 'type': 'head'},
            '172.30.0.1': {'hostname': 'node001', 'type': 'compute'},
            '172.30.0.2': {'hostname': 'node002', 'type': 'compute'},
            '172.30.0.3': {'hostname': 'node003', 'type': 'compute'},
        }
        return host_details
