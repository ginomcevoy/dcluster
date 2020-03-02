import logging
import os

from dcluster import config, logger, networking

from dcluster.cluster import node
from dcluster.plan import simple as simple_plan
from dcluster.docker_facade import DockerNaming, DockerNetworking


class RunningClusterMixin(logger.LoggerMixin):

    def stop(self):
        '''
        Stop the docker cluster, by stopping each container.
        TODO: start this manually again
        '''
        for n in self.ordered_nodes:
            n.container.stop()

    def remove(self):
        '''
        Remove the docker cluster, by removing each container and the network
        '''
        self.stop()
        for n in self.ordered_nodes:
            n.container.remove()

        self.cluster_network.remove()

    def ssh_to_node(self, username, hostname):
        '''
        Connect to a cluster node via SSH.
        TODO Refactor to someplace else, with configuration options.
        '''
        node = self.node_by_name(hostname)
        ssh_command = '/usr/bin/ssh -o "StrictHostKeyChecking=no" -o "GSSAPIAuthentication=no" \
-o "UserKnownHostsFile /dev/null" -o "LogLevel ERROR" %s'

        target = '%s@%s' % (username, node.ip_address)
        full_ssh_command = ssh_command % target
        # subprocess.run(full_ssh_command, shell=True)
        os.system(full_ssh_command)

    def scp_to_node(self, username, hostname, target_dir, files):
        '''
        Send one or more files to a cluster node via SSH.
        TODO Refactor to someplace else, with configuration options.
        '''
        node = self.node_by_name(hostname)

        # determine if "-r" should be added
        rflag = recursive_flag(files)

        scp_command = '/usr/bin/scp -o "StrictHostKeyChecking=no" -o "GSSAPIAuthentication=no" \
            %s %s %s'

        target = '%s@%s:%s' % (username, node.ip_address, target_dir)
        full_scp_command = scp_command % (rflag, ' '.join(files), target)

        self.logger.debug(full_scp_command)
        os.system(full_scp_command)

    def node_by_name(self, hostname):
        '''
        Search the nodes for the node that has the hostname.
        '''
        return next(a_node for a_node in self.ordered_nodes if a_node.hostname == hostname)

    def inject_public_ssh_key(self, public_key_path):
        '''
        Reads the public SSH key specified in the path, and injects it to each container.
        For now, it will inject it to the root user.
        '''
        ssh_target_path = '/root/.ssh'

        with open(public_key_path, 'r') as pk:
            public_key = pk.read()
            public_key = public_key.strip()  # otherwise we get a new line in Python 2.x...
        self.logger.debug('Read public key: %s' % public_key)

        for n in self.ordered_nodes:
            n.inject_public_ssh_key(ssh_target_path, public_key)


class DeployedCluster(simple_plan.SimpleClusterBlueprint, RunningClusterMixin):

    @classmethod
    def from_docker(cls, cluster_name):
        '''
        Returns an instance of SimpleCluster using the name and querying docker for the
        missing data.

        Raises NotDclusterElement if cluster network is not found.
        '''
        log = logging.getLogger()
        log.debug('from_docker %s' % cluster_name)

        # find the network in docker, build dcluster network
        cluster_network = networking.DockerClusterNetworkFactory.from_existing(cluster_name)
        log.debug(cluster_network)

        # find the nodes in the cluster
        docker_network = cluster_network.docker_network
        deployed_nodes = node.DeployedNode.find_for_cluster(cluster_name, docker_network)

        # TODO recover everything (missing network details)?
        partial_cluster_specs = {
            'name': cluster_name,
            'nodes': {n.ip_address: n for n in deployed_nodes},
            'network': {
                'name': cluster_network.network_name,
                'subnet': cluster_network.subnet
            }
        }

        return DeployedCluster(cluster_network, partial_cluster_specs)

    @classmethod
    def list_all(cls):
        '''
        Returns a list of current DockerCluster names (not instances) by querying docker.
        '''
        docker_networks = DockerNetworking.all_dcluster_networks()
        return [DockerNaming.deduce_cluster_name(network.name) for network in docker_networks]


def recursive_flag(files):

    # by default don't pass "-r"
    recursive = ''

    for file in files:
        if os.path.isdir(file):
            # pass "-r"
            recursive = '-r'
            break

    return recursive
