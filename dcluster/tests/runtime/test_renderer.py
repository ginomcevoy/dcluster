from dcluster.config import main_config
from dcluster.runtime import render

from dcluster.tests.test_dcluster import DclusterTest
from dcluster.tests import test_resources


class TestJinjaRenderer(DclusterTest):

    def setUp(self):
        self.resources = test_resources.ResourcesForTest()
        self.maxDiff = None

        templates_dir = main_config.paths('templates')
        self.renderer = render.JinjaRenderer(templates_dir)

    def test_basic_render(self):
        # given a basic cluster specification
        cluster_specs = {
            'nodes': {
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
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            },
            'bootstrap_dir': '/home/giacomo/dcluster/bootstrap'
        }
        template_filename = 'cluster-default.yml.j2'

        # when
        result = self.renderer.render_blueprint(cluster_specs, template_filename)

        # then matches a saved file
        expected = self.resources.expected_docker_compose_simple
        self.assertEqual(result, expected)

    def test_basic_render_with_hostname_alias(self):
        # given a basic cluster specification
        cluster_specs = {
            'nodes': {
                '172.30.0.253': {
                    'hostname': 'head',
                    'hostname_alias': 'head-cool-alias',
                    'container': 'mycluster-head',
                    'image': 'centos7:ssh',
                    'ip_address': '172.30.0.253',
                    'role': 'head'
                },
                '172.30.0.1': {
                    'hostname': 'node001',
                    'hostname_alias': 'node001-cool-alias',
                    'container': 'mycluster-node001',
                    'image': 'centos7:ssh',
                    'ip_address': '172.30.0.1',
                    'role': 'compute'
                },
                '172.30.0.2': {
                    'hostname': 'node002',
                    'hostname_alias': 'node002-cool-alias',
                    'container': 'mycluster-node002',
                    'image': 'centos7:ssh',
                    'ip_address': '172.30.0.2',
                    'role': 'compute'
                }
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            },
            'bootstrap_dir': '/home/giacomo/dcluster/bootstrap'
        }
        template_filename = 'cluster-default.yml.j2'

        # when
        result = self.renderer.render_blueprint(cluster_specs, template_filename)

        # then matches a saved file
        expected = self.resources.expected_docker_compose_simple_hostname_alias
        self.assertEqual(result, expected)

    def test_basic_render_with_systemctl(self):
        # given a basic cluster specification but systemctl=True
        cluster_specs = {
            'nodes': {
                '172.30.0.253': {
                    'hostname': 'head',
                    'container': 'mycluster-head',
                    'image': 'centos7:ssh',
                    'ip_address': '172.30.0.253',
                    'role': 'head',
                    'systemctl': True
                },
                '172.30.0.1': {
                    'hostname': 'node001',
                    'container': 'mycluster-node001',
                    'image': 'centos7:ssh',
                    'ip_address': '172.30.0.1',
                    'role': 'compute',
                    'systemctl': True
                },
                '172.30.0.2': {
                    'hostname': 'node002',
                    'container': 'mycluster-node002',
                    'image': 'centos7:ssh',
                    'ip_address': '172.30.0.2',
                    'role': 'compute',
                    'systemctl': True
                }
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            },
            'bootstrap_dir': '/home/giacomo/dcluster/bootstrap'
        }
        template_filename = 'cluster-default.yml.j2'

        # when
        result = self.renderer.render_blueprint(cluster_specs, template_filename)

        # then matches a saved file
        expected = self.resources.expected_docker_compose_simple_priv
        self.assertEqual(result, expected)

    def test_slurm_render(self):
        # given a cluster specification for Slurm
        cluster_specs = {
            'nodes': {
                '172.30.0.253': {
                    'hostname': 'head',
                    'container': 'mycluster-head',
                    'image': 'centos7:slurmctld',
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
                    'image': 'centos7:slurmd',
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
                    'image': 'centos7:slurmd',
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
            'bootstrap_dir': '/home/giacomo/dcluster/bootstrap'
        }
        template_filename = 'cluster-default.yml.j2'

        # when
        result = self.renderer.render_blueprint(cluster_specs, template_filename)

        # then matches a saved file
        expected = self.resources.expected_docker_compose_slurm
        self.assertEqual(result, expected)

    def test_render_extended_simplified(self):
        # given a cluster specification for Slurm but without the extended parts
        cluster_specs = {
            'nodes': {
                '172.30.0.253': {
                    'hostname': 'head',
                    'container': 'mycluster-head',
                    'image': 'centos7:slurmctld',
                    'ip_address': '172.30.0.253',
                    'role': 'head',
                },
                '172.30.0.1': {
                    'hostname': 'node001',
                    'container': 'mycluster-node001',
                    'image': 'centos7:slurmd',
                    'ip_address': '172.30.0.1',
                    'role': 'compute',
                },
                '172.30.0.2': {
                    'hostname': 'node002',
                    'container': 'mycluster-node002',
                    'image': 'centos7:slurmd',
                    'ip_address': '172.30.0.2',
                    'role': 'compute',
                }
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            },
            'bootstrap_dir': '/home/giacomo/dcluster/bootstrap'
        }
        template_filename = 'cluster-default.yml.j2'

        # when
        result = self.renderer.render_blueprint(cluster_specs, template_filename)

        # then matches a saved file
        expected = self.resources.expected_render_extended_simplified
        self.assertEqual(result, expected)
