import collections
import unittest

from dcluster import config
from dcluster.compose import simple as simple_compose

from dcluster.tests import test_resources


class TestClusterComposerSimple(unittest.TestCase):

    def setUp(self):
        self.resources = test_resources.ResourcesForTest()
        self.maxDiff = None

        templates_dir = config.paths('templates')
        print(templates_dir)
        self.composer = simple_compose.ClusterComposerSimple('', templates_dir)

    def test_build_definition(self):
        # given a cluster specification
        cluster_specs = {
            'nodes': collections.OrderedDict({
                '172.30.0.253': {
                    'hostname': 'head',
                    'container': 'mycluster-head',
                    'image': 'centos7:ssh',
                    'ip_address': '172.30.0.253',
                    'role': 'head'
                },
                '172.30.0.1': {
                    'hostname': 'node001',
                    'container': 'mycluster-node001',
                    'image': 'centos7:ssh',
                    'ip_address': '172.30.0.1',
                    'role': 'compute'
                },
                '172.30.0.2': {
                    'hostname': 'node002',
                    'container': 'mycluster-node002',
                    'image': 'centos7:ssh',
                    'ip_address': '172.30.0.2',
                    'role': 'compute'
                }
            }),
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            }
        }
        template_filename = 'cluster-simple.yml.j2'

        # when
        result = self.composer.build_definition(cluster_specs, template_filename)

        # then matches a saved file
        expected = self.resources.expected_docker_compose_simple
        self.assertEqual(result, expected)
