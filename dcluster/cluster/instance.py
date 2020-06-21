import logging
import os

from .blueprint import ClusterBlueprint
from .format import TextFormatterBasic

from dcluster.node import instance as node_instance
from dcluster.infra.docker_facade import DockerNaming, DockerNetworking
from dcluster.infra import networking

from dcluster.util import logger


class RunningClusterMixin(logger.LoggerMixin):
    '''
    A mixin class that adds functionality applicable to clusters that have already been
    deployed (as opposed to planned clusters).
    '''

    def stop(self):
        '''
        Stop the docker cluster, by stopping each container. Does not remove the cluster network.
        The stopped containers can be started again either by Docker CLI (docker start <container>)
        or by using the start() method.
        '''
        for n in self.ordered_nodes:
            n.container.stop()

    def start(self):
        self.logger.debug('Starting containers of cluster: {}'.format(self.name))

        for node in self.ordered_nodes:
            self.logger.debug('Found running node for [{}]: {}'.format(self.name, node))

        # get stopped containers by querying containers attached to the network
        stopped_containers = self.cluster_network.stopped_containers
        self.logger.debug('Found stopped containers: {}'.format(stopped_containers))

        if not stopped_containers:
            # there are no stopped containers
            # no new containers will get started
            # output depends on existing running containers
            if self.ordered_nodes:

                # inform user that there are no stopped containers, cluster is already up
                self.logger.info('No stopped containers found for [{}]'.format(self.name))

                for node in self.ordered_nodes:
                    self.logger.info('Found running node for [{}]: {}'.format(self.name, node))

            else:

                # no stopped containers and no running containers, probably something isn't right
                log_msg = 'No stopped containers and no running containers found for {}!'
                self.logger.warn(log_msg.format(self.name))

        else:
            # Found stopped containers, start them without mentioning previously running containers
            for c in stopped_containers:
                c.start()

        # create a new instance of this cluster, and output it
        # hopefully failed attempts at starting containers will be 'caught' here by not showing
        # the failed containers...
        updated_cluster = DeployedCluster.from_docker(self.name)
        formatter = TextFormatterBasic()
        updated_state = updated_cluster.format(formatter)
        print(updated_state)

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


class DeployedCluster(ClusterBlueprint, RunningClusterMixin):
    '''
    Represents a cluster that has already been deployed by docker.

    This means that the cluster has already been planned and deployed, and the creation command
    exited. As a result (since dcluster is not a daemon and keeps no state), any information about
    the cluster needs to be retrieved from Docker. This limits the amount of information we can
    retrieve.

    It only makes sense to create an instance of this class using from_docker() factory method.
    '''

    @classmethod
    def from_docker(cls, cluster_name):
        '''
        Returns an instance of DeployedCluster using the name and querying docker for the
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
        deployed_nodes = node_instance.DeployedNode.find_for_cluster(cluster_name, docker_network)

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
    '''
    Detects whether to add '-r' to scp to handle recursive copy.
    Will add -r if at least one of the inputs is a directory.

    TODO move this to a better place. (dcluster.node.ssh?)
    '''

    # by default don't pass "-r"
    recursive = ''

    for file in files:
        if os.path.isdir(file):
            # pass "-r"
            recursive = '-r'
            break

    return recursive
