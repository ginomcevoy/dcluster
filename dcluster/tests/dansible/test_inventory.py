import yaml

from dcluster.tests.test_dcluster import DclusterTest
from dcluster.tests import test_resources

from dcluster.dansible import inventory
from dcluster.node import BasicPlannedNode

class TestCreateAnsibleInventory(DclusterTest):

    def setUp(self):
        resources = test_resources.ResourcesForTest()
        self.inventory = inventory.AnsibleInventory(self.blueprint_as_dict())
        self.expected = resources.expected_inventory
        self.maxDiff = None

    def test_hosts(self):
        created = self.inventory.create_dict()
        self.assertEqual(created['all']['hosts'], self.expected['all']['hosts'])

    def test_head_present(self):
        created = self.inventory.create_dict()

        self.assertTrue('children' in created['all'].keys())
        self.assertTrue('head' in created['all']['children'].keys())

    def test_head_contents(self):
        created = self.inventory.create_dict()

        self.assertEqual(created['all']['children']['head'],
                         self.expected['all']['children']['head'])

    def test_complete_output(self):
        created = self.inventory.create_dict()
        print(created)
        self.assertEqual(created, self.expected)

    def test_yaml_output(self):
        output_filename = '/tmp/dcluster_output_cluster.yml'
        self.inventory.to_yaml(output_filename)

        with open(output_filename, 'r') as of:
            actual_output = yaml.load(of, Loader=yaml.SafeLoader)

        self.assertEqual(actual_output, self.expected)

    def host_details(self):
        host_details = {
            '172.30.0.253':
                {'hostname': 'slurmctld', 'type': 'head'},
            '172.30.0.1': {'hostname': 'node001', 'type': 'compute'},
            '172.30.0.2': {'hostname': 'node002', 'type': 'compute'},
            '172.30.0.3': {'hostname': 'node003', 'type': 'compute'},
        }
        return host_details

    def blueprint_as_dict(self):
        return {
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
