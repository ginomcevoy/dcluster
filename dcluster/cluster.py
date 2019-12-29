import logging
# import subprocess
import os

from . import networking
from .docker_facade import Node, DockerNaming, DockerNetworking


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
        Stop the docker cluster, by stopping each container and removing the network.
        '''
        for node in self.nodes:
            node.container.stop()

        self.cluster_network.remove()

    def ssh_to_node(self, hostname):
        '''
        Connect to a cluster node via SSH. Refactor to someplace else, with configuration
        options, when we have an installer.
        '''
        node = self.node_by_name(hostname)
        ip_address = DockerNetworking.container_ip_address(node.container, self.docker_network)
        ssh_command = '/usr/bin/ssh -o "StrictHostKeyChecking=no" -o "GSSAPIAuthentication=no" \
-o "UserKnownHostsFile /dev/null" -o "LogLevel ERROR" %s'

        target = 'ci-user@%s' % ip_address
        full_ssh_command = ssh_command % target
        # subprocess.run(full_ssh_command, shell=True)
        os.system(full_ssh_command)

    def node_by_name(self, hostname):
        '''
        Search the nodes for the node that has the hostname.
        '''
        return next(node for node in self.nodes if node.hostname == hostname)

    @classmethod
    def create_from_existing(cls, cluster_name):
        '''
        Returns an instance of DockerCluster using the name and querying docker for the
        missing data.

        Raises NotDclusterElement if cluster network is not found.
        '''
        log = logging.getLogger()
        log.debug('create_from_existing %s' % cluster_name)

        # find the network in docker, build dcluster network
        cluster_network = networking.DockerClusterNetworkFactory.from_existing(cluster_name)
        log.debug(cluster_network)

        # find the nodes in the cluster
        nodes = DockerNetworking.find_nodes_for_cluster(cluster_name,
                                                        cluster_network.docker_network)

        return DockerCluster(cluster_name, cluster_network, nodes)

    @classmethod
    def list_all(cls):
        '''
        Returns a list of current DockerCluster names (not instances) by querying docker.
        '''
        docker_networks = DockerNetworking.all_dcluster_networks()
        return [DockerNaming.deduce_cluster_name(network.name) for network in docker_networks]


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
        lines[4] = node_format.format(*Node._fields)
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
