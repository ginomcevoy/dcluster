import os
import unittest

from dcluster import compose

from config import dcluster_config
from . import test_resources


class TestClusterComposer(unittest.TestCase):

    def setUp(self):
        self.resources = test_resources.TestResources()
        self.maxDiff = None

        templates_dir = dcluster_config.get('templates_dir')
        # template_path = os.path.join(templates_dir, 'cluster-simple.yml.j2')
        self.composer = compose.ClusterComposer('', templates_dir)

    def test_build_definition(self):
        # given a cluster specification
        cluster_specs = {
            'nodes': {
                '172.30.0.253': {
                    'hostname': 'head',
                    'container': 'mycluster-head',
                    'ip_address': '172.30.0.253',
                    'type': 'head'
                },
                '172.30.0.1': {
                    'hostname': 'node001',
                    'container': 'mycluster-node001',
                    'ip_address': '172.30.0.1',
                    'type': 'compute'
                },
                '172.30.0.2': {
                    'hostname': 'node002',
                    'container': 'mycluster-node002',
                    'ip_address': '172.30.0.2',
                    'type': 'compute'
                }
            },
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
        print(result)

        # then matches a saved file
        expected = self.resources.expected_docker_compose_simple
        self.assertEqual(result, expected)
