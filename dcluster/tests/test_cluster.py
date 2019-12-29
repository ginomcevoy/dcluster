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

       hostname      ip_address           container_name
'''
        self.assertEqual(result, expected)

    def test_format_three_nodes(self):
        # given
        cluster_dict = {
            'name': 'testcluster',
            'network': '172.30.0.0/24',
            'nodes': {
                'node001': cluster.Node('node001', '172.30.0.1', 'testcluster-node001'),
                'node002': cluster.Node('node002', '172.30.0.2', 'testcluster-node002'),
                'head': cluster.Node('head', '172.30.0.253', 'testcluster-head'),
                'gateway': cluster.Node('gateway', '172.30.0.254', ''),
            }
        }

        # when
        result = self.formatter.format(cluster_dict)

        # then
        expected = '''Cluster: testcluster
------------------------
Network: 172.30.0.0/24

       hostname      ip_address           container_name
        node001      172.30.0.1      testcluster-node001
        node002      172.30.0.2      testcluster-node002
           head    172.30.0.253         testcluster-head
        gateway    172.30.0.254                         
'''
        self.maxDiff = None
        self.assertEqual(result, expected)
