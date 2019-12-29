import unittest


from dcluster import cluster


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
        return cluster.Node(hostname, ip_address, ContainerStub(container_name))


class ContainerStub:
    '''
    This stubs the real Docker container, it has a name
    '''

    def __init__(self, name):
        self.name = name