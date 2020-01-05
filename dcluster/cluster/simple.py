import logging
import os
from operator import attrgetter

from dcluster import config, logger, networking

from dcluster.cluster import node
from dcluster.compose import simple as simple_compose
from dcluster.docker_facade import DockerNaming, DockerNetworking


class SimplePlanner(logger.LoggerMixin):

    def __init__(self):
        self.templates_dir = config.paths('templates')
        self.cluster_config = config.cluster('simple')

    def create_network(self, request):
        return networking.create(request.name)

    def plan(self, simple_request):

        cluster_network = self.create_network(simple_request)
        cluster_specs = self.build_specs(simple_request, cluster_network)

        return SimpleCluster(cluster_network, cluster_specs)

    def build_specs(self, simple_request, cluster_network):
        '''
        Creates a dictionary of node specs that is needed to later use docker-compose.
        Since we are only building a single type of cluster, we can leave this here.

        A cluster always has a single head, and zero or more compute nodes, depending
        on compute_count.

        Example output: for compute_count = 3, add a head node and 3 compute nodes:

        cluster_specs = {
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': node.PlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos7:ssh',
                    ip_address='172.30.0.253',
                    role='head'),
                '172.30.0.1': node.PlannedNode(
                    hostname='node001',
                    container='mycluster-node001',
                    image='centos7:ssh',
                    ip_address='172.30.0.1',
                    role='compute'),
                '172.30.0.2': node.PlannedNode(
                    hostname='node002',
                    container='mycluster-node002',
                    image='centos7:ssh',
                    ip_address='172.30.0.2',
                    role='compute'),
                '172.30.0.3': node.PlannedNode(
                    hostname='node003',
                    container='mycluster-node003',
                    image='centos7:ssh',
                    ip_address='172.30.0.3',
                    role='compute')
            },
            'network': {
                'name': 'dcluster-mycluster',
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            }
        }
        '''

        cluster_name = simple_request.name
        head_ip = cluster_network.head_ip()
        head_hostname = self.cluster_config['head']['hostname']
        head_image = self.cluster_config['head']['image']

        # always have a head and a network
        head_entry = self.create_node_entry(cluster_name, head_hostname, head_ip,
                                            head_image, 'head')
        network_entry = cluster_network.as_dict()

        cluster_specs = {
            'name': cluster_name,
            'nodes': {
                head_ip: head_entry
            },
            'network': network_entry
        }

        # add compute nodes, should raise NetworkSubnetTooSmall if there are not enough IPs
        compute_ips = cluster_network.compute_ips(simple_request.compute_count)
        compute_image = self.cluster_config['compute']['image']

        for index, compute_ip in enumerate(compute_ips):

            compute_hostname = self.create_compute_hostname(index)
            node_entry = self.create_node_entry(cluster_name, compute_hostname,
                                                compute_ip, compute_image, 'compute')
            cluster_specs['nodes'][compute_ip] = node_entry

        return cluster_specs

    def create_compute_hostname(self, index):
        '''
        Returns the hostname of a compute node given its index.

        Ex.
        0 -> node001
        1 -> node002
        '''
        name_prefix = self.cluster_config['compute']['hostname']['prefix']
        suffix_len = self.cluster_config['compute']['hostname']['suffix_len']

        suffix_str = '{0:0%sd}' % str(suffix_len)
        suffix = suffix_str.format(index + 1)
        return name_prefix + suffix

    def create_node_entry(self, cluster_name, hostname, ip_address, image, role):
        '''
        Create an entry for node specs. The container name is inferred from the hostname.
        '''

        container_name = DockerNaming.create_container_name(cluster_name, hostname)

        return node.PlannedNode(hostname=hostname,
                                container=container_name,
                                image=image,
                                ip_address=ip_address,
                                role=role)


class SimplePlan(object):

    def __init__(self, cluster_network, cluster_specs):
        self.cluster_network = cluster_network
        self.cluster_specs = cluster_specs

        # small initialization to have a list of nodes handy
        ordered_node_ips = sorted(self.cluster_specs['nodes'].keys())
        self.ordered_nodes = [
            self.cluster_specs['nodes'][ordered_ip]
            for ordered_ip
            in ordered_node_ips
        ]

    @property
    def name(self):
        return self.cluster_specs['name']

    def nodes_by_role(self, role):
        '''
        Returns a list of the nodes that are of some role
        '''
        return [
            n
            for n in self.ordered_nodes
            if n.role == role
        ]

    @property
    def head_node(self):
        return self.nodes_by_role('head')[0]

    @property
    def gateway_node(self):
        return self.nodes_by_role('gateway')[0]

    @property
    def compute_nodes(self):
        return self.nodes_by_role('compute')

    def as_dict(self):
        '''
        Dictionary representation of a Docker cluster.
        '''
        return self.cluster_specs

    def format(self, formatter):
        '''
        Format the cluster to some representation, e.g. as text.
        '''
        return formatter.format(self.as_dict())


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


class SimpleCluster(SimplePlan, RunningClusterMixin):

    def __init__(self, cluster_network, cluster_specs):
        super(SimpleCluster, self).__init__(cluster_network, cluster_specs)
        self.templates_dir = config.paths('templates')

    def deploy(self, basepath):

        # TODO receive composer from planner, use self.composer
        # Create classes to reflect that "from_docker" clusters cannot be deployed again

        compose_path = os.path.join(basepath, self.name)
        composer = simple_compose.ClusterComposerSimple(compose_path, self.templates_dir)
        definition = composer.build_definition(self.cluster_specs, 'cluster-simple.yml.j2')
        composer.compose(definition)

        log_msg = 'Docker cluster %s -  %s created!'
        self.logger.info(log_msg % (self.cluster_network.network_name, self.cluster_network))

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

        return SimpleCluster(cluster_network, partial_cluster_specs)

    @classmethod
    def list_all(cls):
        '''
        Returns a list of current DockerCluster names (not instances) by querying docker.
        '''
        docker_networks = DockerNetworking.all_dcluster_networks()
        return [DockerNaming.deduce_cluster_name(network.name) for network in docker_networks]


class SimpleFormatter(object):
    '''
    Formats a simple cluster as text.
    '''

    def format(self, cluster_dict):
        lines = [''] * 6
        lines[0] = 'Cluster: %s' % cluster_dict['name']
        lines[1] = '-' * 24
        lines[2] = 'Network: %s' % cluster_dict['network']['subnet']
        lines[3] = ''

        node_format = '  {:15}{:16}{:25}'

        # header of nodes
        lines[4] = node_format.format('hostname', 'ip_address', 'container')
        lines[5] = '  ' + '-' * 48

        sorted_node_info = sorted(cluster_dict['nodes'].values(), key=attrgetter('hostname'))

        node_lines = [
            # format namedtuple contents
            node_format.format(node.hostname, node.ip_address, node.container.name)
            for node
            in sorted_node_info
        ]

        lines.extend(node_lines)
        lines.append('')
        return '\n'.join(lines)
