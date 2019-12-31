import collections
import ipaddress
import unittest


from dcluster import cluster, networking
from dcluster import docker_facade


class TestBuildNodeSpecsSimple(unittest.TestCase):
    '''
    Unit tests for cluster.DockerClusterBuilder.build_simple_specs
    '''

    def setUp(self):
        self.builder = cluster.DockerClusterBuilder()

    def test_zero_compute_nodes(self):
        '''
        Cluster without compute nodes, just the head
        '''
        # given
        compute_nodes = 0
        cluster_specs_simple = self.simple_request('mycluster', compute_nodes)
        cluster_network = self.stub_network('172.30.0.0/24', cluster_specs_simple)

        # when
        result = self.builder.build_simple_specs(cluster_specs_simple, cluster_network)

        # then
        expected = {
            'nodes': {
                '172.30.0.253': {
                    'hostname': 'head',
                    'container': 'mycluster-head',
                    'ip_address': '172.30.0.253',
                    'type': 'head'
                }
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            }
        }
        self.assertEqual(result, expected)

    def test_zero_compute_nodes_small_subnet(self):
        '''
        Cluster without compute nodes, just the head, small subnet
        '''
        # given
        compute_nodes = 0
        cluster_specs_simple = self.simple_request('mycluster', compute_nodes)
        cluster_network = self.stub_network('172.30.1.0/25', cluster_specs_simple)

        # when
        result = self.builder.build_simple_specs(cluster_specs_simple, cluster_network)

        # then
        expected = {
            'nodes': {
                '172.30.1.125': {
                    'hostname': 'head',
                    'container': 'mycluster-head',
                    'ip_address': '172.30.1.125',
                    'type': 'head'
                }
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.1.0/25',
                'gateway': 'gateway',
                'gateway_ip': '172.30.1.126'
            }
        }
        self.assertEqual(result, expected)

    def test_one_compute_node(self):
        '''
        Cluster with one compute node
        '''
        # given
        compute_nodes = 1
        cluster_specs_simple = self.simple_request('mycluster', compute_nodes)
        cluster_network = self.stub_network('172.30.0.0/24', cluster_specs_simple)

        # when
        result = self.builder.build_simple_specs(cluster_specs_simple, cluster_network)

        # then
        expected = {
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
                }
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            }
        }
        self.assertEqual(result, expected)

    def test_three_compute_nodes(self):
        '''
        Cluster with three compute nodes
        '''
        # given
        compute_nodes = 3
        cluster_specs_simple = self.simple_request('mycluster', compute_nodes)
        cluster_network = self.stub_network('172.30.0.0/24', cluster_specs_simple)

        # when
        result = self.builder.build_simple_specs(cluster_specs_simple, cluster_network)

        # then
        expected = {
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
                },
                '172.30.0.3': {
                    'hostname': 'node003',
                    'container': 'mycluster-node003',
                    'ip_address': '172.30.0.3',
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
        self.assertEqual(result, expected)

    def simple_request(self, name, compute_count):
        return cluster.ClusterRequestSimple(name, compute_count)

    def stub_network(self, subnet_str, cluster_specs_simple):
        subnet = ipaddress.ip_network(subnet_str)
        return networking.ClusterNetwork(subnet, cluster_specs_simple.name)


class DockerClusterFormatterTextTest(unittest.TestCase):
    '''
    Unit tests for cluster.DockerClusterFormatterText
    '''

    def setUp(self):
        self.formatter = cluster.DockerClusterFormatterText()

    def test_format_no_nodes(self):
        # given
        cluster_dict = {
            'name': 'testcluster',
            'network': '172.30.0.0/24',
            'nodes': {}
        }

        # when
        result = self.formatter.format(cluster_dict)

        # then
        expected = '''Cluster: testcluster
------------------------
Network: 172.30.0.0/24

  hostname       ip_address      container                
  ------------------------------------------------
'''
        self.assertEqual(result, expected)

    def test_format_three_nodes(self):
        # given
        cluster_dict = {
            'name': 'testcluster',
            'network': '172.30.0.0/24',
            'nodes': {
                'node001': self.node_stub('node001', '172.30.0.1', 'testcluster-node001'),
                'node002': self.node_stub('node002', '172.30.0.2', 'testcluster-node002'),
                'head': self.node_stub('head', '172.30.0.253', 'testcluster-head'),
                'gateway': self.node_stub('gateway', '172.30.0.254', ''),
            }
        }

        # when
        result = self.formatter.format(cluster_dict)

        # then
        expected = '''Cluster: testcluster
------------------------
Network: 172.30.0.0/24

  hostname       ip_address      container                
  ------------------------------------------------
  node001        172.30.0.1      testcluster-node001      
  node002        172.30.0.2      testcluster-node002      
  head           172.30.0.253    testcluster-head         
  gateway        172.30.0.254                             
'''
        self.maxDiff = None
        self.assertEqual(result, expected)

    def node_stub(self, hostname, ip_address, container_name):
        NodeStub = collections.namedtuple('NodeStub', 'hostname, ip_address, container')
        return NodeStub(hostname, ip_address, ContainerStub(container_name))


class ContainerStub:
    '''
    This stubs the real Docker container, it has a name
    '''

    def __init__(self, name):
        self.name = name
