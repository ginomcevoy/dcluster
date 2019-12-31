import logging
# import subprocess
from collections import namedtuple
import os

from . import compose
from . import config
from . import networking

from .docker_facade import ClusterNode, DockerNaming, DockerNetworking


# represents a 'simple' cluster with the specified count of compute nodes.
# it should also have a head node.
ClusterRequestSimple = namedtuple('ClusterRequestSimple', ['name', 'compute_count'])


def create(cluster_request, basepath):
    '''
    Convenience method to create a docker cluster, calls the builder with default options
    '''
    return DockerClusterBuilder().build(cluster_request, basepath)


class DockerCluster(object):

    def __init__(self, cluster_name, cluster_network, nodes):
        self.name = cluster_name
        self.cluster_network = cluster_network
        self.nodes = nodes

    def nodes_by_type(self, node_type):
        '''
        Returns a list of the nodes that are of some type
        '''
        return [
            node
            for node in self.nodes
            if node.type == node_type
        ]

    @property
    def head_node(self):
        return self.nodes_by_type('head')[0]

    @property
    def gateway_node(self):
        return self.nodes_by_type('gateway')[0]

    @property
    def compute_nodes(self):
        return self.nodes_by_type('compute')

    @property
    def docker_network(self):
        '''
        Ugly for now...
        '''
        return self.cluster_network.docker_network

    def as_dict(self):
        '''
        Dictionary representation of a Docker cluster.
        '''
        d = {
            'name': self.name,
            'network': str(self.cluster_network),
            'nodes': {}
        }
        for node in self.nodes:
            d['nodes'][node.hostname] = node

        return d

    def format(self, formatter):
        '''
        Format the cluster to some representation, e.g. as text.
        '''
        return formatter.format(self.as_dict())

    def stop(self):
        '''
        Stop the docker cluster, by stopping each container.
        TODO: start this manually again
        '''
        for node in self.nodes:
            node.container.stop()

    def remove(self):
        '''
        Remove the docker cluster, by removing each container and the network
        '''
        self.stop()
        for node in self.nodes:
            node.container.remove()

        self.cluster_network.remove()

    def ssh_to_node(self, hostname):
        '''
        Connect to a cluster node via SSH. Refactor to someplace else, with configuration
        options, when we have an installer.
        '''
        node = self.node_by_name(hostname)
        ssh_command = '/usr/bin/ssh -o "StrictHostKeyChecking=no" -o "GSSAPIAuthentication=no" \
-o "UserKnownHostsFile /dev/null" -o "LogLevel ERROR" %s'

        ssh_user = config.prefs('ssh_user')
        target = '%s@%s' % (ssh_user, node.ip_address)
        full_ssh_command = ssh_command % target
        # subprocess.run(full_ssh_command, shell=True)
        os.system(full_ssh_command)

    def node_by_name(self, hostname):
        '''
        Search the nodes for the node that has the hostname.
        '''
        return next(node for node in self.nodes if node.hostname == hostname)

    @classmethod
    def from_docker(cls, cluster_name):
        '''
        Returns an instance of DockerCluster using the name and querying docker for the
        missing data.

        Raises NotDclusterElement if cluster network is not found.
        '''
        log = logging.getLogger()
        log.debug('from_docker %s' % cluster_name)

        # find the network in docker, build dcluster network
        cluster_network = networking.DockerClusterNetworkFactory.from_existing(cluster_name)
        log.debug(cluster_network)

        # find the nodes in the cluster
        # nodes = DockerNetworking.find_nodes_for_cluster(cluster_name,
        #                                                 cluster_network.docker_network)
        nodes = ClusterNode.find_for_cluster(cluster_name, cluster_network.docker_network)

        return DockerCluster(cluster_name, cluster_network, nodes)

    @classmethod
    def list_all(cls):
        '''
        Returns a list of current DockerCluster names (not instances) by querying docker.
        '''
        docker_networks = DockerNetworking.all_dcluster_networks()
        return [DockerNaming.deduce_cluster_name(network.name) for network in docker_networks]


class DockerClusterBuilder(object):

    def __init__(self):
        self.build_funcs = {
            'ClusterRequestSimple': self.build_simple
        }
        self.log = logging.getLogger()

    def build(self, cluster_request, basepath):
        '''
        Creates a new docker cluster based on the specified request.
        '''
        # for now, only simple
        build_func = self.build_funcs[type(cluster_request).__name__]
        return build_func(cluster_request, basepath)

    def build_simple(self, simple_request, basepath):
        '''
        Creates a simple cluster. It has the specified compute count and a head node.
        The network is created first, then the containers.

        This does not return an instance of DockerCluster yet...
        '''
        # create the cluster specification
        cluster_network = networking.create(simple_request.name)
        cluster_specs = self.build_simple_specs(simple_request, cluster_network)

        # create the containers based on the specification
        compose_path = os.path.join(basepath, simple_request.name)
        templates_dir = config.internal('templates_dir')
        composer = compose.ClusterComposer(compose_path, templates_dir)
        definition = composer.build_definition(cluster_specs, 'cluster-simple.yml.j2')
        composer.compose(definition)

        log_msg = 'Docker cluster %s -  %s created!'
        self.log.info(log_msg % (cluster_network.network_name, cluster_network))

    def build_simple_specs(self, simple_request, cluster_network):
        '''
        Creates a dictionary of node specs that is needed to later use docker-compose.
        Since we are only building a single type of cluster, we can leave this here.

        A cluster always has a single head, and zero or more compute nodes, depending
        on compute_count.

        Example output: for compute_count = 3, add a head node and 3 compute nodes:

        cluster_specs = {
            'nodes' : {
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
            }
            'network': {
                'name': 'dcluster-mycluster',
                'ip_address': '172.30.0.0/24'
                'gateway_hostname': 'gateway'
                'gateway_ip': '172.30.0.254'
            }
        }
        '''

        cluster_name = simple_request.name
        head_ip = cluster_network.head_ip()
        head_hostname = config.naming('head_name')

        # always have a head and a network
        head_entry = self.create_node_entry(cluster_name, head_hostname, head_ip, 'head')
        network_entry = cluster_network.as_dict()

        cluster_specs = {
            'nodes': {
                head_ip: head_entry
            },
            'network': network_entry
        }

        # add compute nodes, should raise NetworkSubnetTooSmall if there are not enough IPs
        compute_ips = cluster_network.compute_ips(simple_request.compute_count)

        for index, compute_ip in enumerate(compute_ips):

            compute_hostname = self.create_compute_hostname(index)
            node_entry = self.create_node_entry(cluster_name, compute_hostname,
                                                compute_ip, 'compute')
            cluster_specs['nodes'][compute_ip] = node_entry

        return cluster_specs

    def create_compute_hostname(self, index):
        '''
        Returns the hostname of a compute node given its index.

        Ex.
        0 -> node001
        1 -> node002
        '''
        suffix_str = '{0:0%sd}' % str(config.naming('compute_suffix_len'))
        suffix = suffix_str.format(index + 1)
        return config.naming('compute_prefix') + suffix

    def create_node_entry(self, cluster_name, hostname, ip_address, node_type):
        '''
        Create an entry for node specs. The container name is inferred from the hostname.
        '''

        container_name = DockerNaming.create_container_name(cluster_name, hostname)

        return {
            'hostname': hostname,
            'container': container_name,
            'ip_address': ip_address,
            'type': node_type
        }


class DockerClusterFormatterText(object):
    '''
    Formats a docker cluster as text.
    '''

    def format(self, cluster_dict):
        lines = [''] * 6
        lines[0] = 'Cluster: %s' % cluster_dict['name']
        lines[1] = '-' * 24
        lines[2] = 'Network: %s' % cluster_dict['network']
        lines[3] = ''

        node_format = '  {:15}{:16}{:25}'

        # header of nodes
        lines[4] = node_format.format('hostname', 'ip_address', 'container')
        lines[5] = '  ' + '-' * 48

        node_lines = [
            # format namedtuple contents
            node_format.format(node.hostname, node.ip_address, node.container.name)
            for node
            in cluster_dict['nodes'].values()
        ]

        lines.extend(node_lines)
        lines.append('')
        return '\n'.join(lines)
