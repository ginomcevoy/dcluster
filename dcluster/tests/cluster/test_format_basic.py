import collections

from dcluster.tests.test_dcluster import DclusterTest
from dcluster.cluster.format import TextFormatterBasic


class TextFormatterBasicTest(DclusterTest):
    '''
    Unit tests for cluster.format.TextFormatterBasic
    '''

    def setUp(self):
        self.formatter = TextFormatterBasic()

    def test_format_no_nodes(self):
        # given
        cluster_dict = {
            'name': 'testcluster',
            'network': {'subnet': '172.30.0.0/24'},
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
            'network': {'subnet': '172.30.0.0/24'},
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
  gateway        172.30.0.254                             
  head           172.30.0.253    testcluster-head         
  node001        172.30.0.1      testcluster-node001      
  node002        172.30.0.2      testcluster-node002      
'''
        self.maxDiff = None
        self.assertEqual(result, expected)

    def node_stub(self, hostname, ip_address, container_name):
        NodeStub = collections.namedtuple('NodeStub', 'hostname, ip_address, container')
        return NodeStub(hostname, ip_address, ContainerStub(container_name))


class ContainerStub(object):
    '''
    This stubs the real Docker container, it has a name
    '''

    def __init__(self, name):
        self.name = name
