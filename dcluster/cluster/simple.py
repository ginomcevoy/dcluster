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
        return next(a_node for a_node in self.ordered_nodes if a_node.hostname == hostname)


class DeployedCluster(simple_plan.SimpleClusterBlueprint, RunningClusterMixin):

    # def deploy(self, basepath):

        # TODO receive composer from planner, use self.composer
        # Create classes to reflect that "from_docker" clusters cannot be deployed again

        # compose_path = os.path.join(basepath, self.name)
        # composer = simple_compose.ClusterComposerSimple(compose_path, self.templates_dir)
        # definition = composer.build_definition(self.cluster_specs, 'cluster-simple.yml.j2')
        # composer.compose(definition)

        # log_msg = 'Docker cluster %s -  %s created!'
        # self.logger.info(log_msg % (self.cluster_network.network_name, self.cluster_network))

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

        template = config.for_cluster('simple')['template']  # eww

        return DeployedCluster(cluster_network, partial_cluster_specs, template)

    @classmethod
    def list_all(cls):
        '''
        Returns a list of current DockerCluster names (not instances) by querying docker.
        '''
        docker_networks = DockerNetworking.all_dcluster_networks()
        return [DockerNaming.deduce_cluster_name(network.name) for network in docker_networks]
