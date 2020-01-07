import collections
import unittest

from dcluster import config
from dcluster.cluster import render

from dcluster.tests import test_resources


class TestJinjaRenderer(unittest.TestCase):

    def setUp(self):
        self.resources = test_resources.ResourcesForTest()
        self.maxDiff = None

        templates_dir = config.paths('templates')
        self.renderer = render.JinjaRenderer(templates_dir)

    def test_simple_render(self):
        # given a simple cluster specification
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
        result = self.renderer.render_blueprint(cluster_specs, template_filename)

        # then matches a saved file
        expected = self.resources.expected_docker_compose_simple
        self.assertEqual(result, expected)

    def test_slurm_render(self):
        # given a cluster specification for Slurm
        cluster_specs = {
            'nodes': collections.OrderedDict({
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
            }),
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
        template_filename = 'cluster-slurm.yml.j2'

        # when
        result = self.renderer.render_blueprint(cluster_specs, template_filename)

        # then matches a saved file
        expected = self.resources.expected_docker_compose_slurm
        self.assertEqual(result, expected)
