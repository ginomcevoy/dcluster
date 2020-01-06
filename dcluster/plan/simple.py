from operator import attrgetter

from dcluster import logger, util
from dcluster.docker_facade import DockerNaming

from . import PlannedNode


class SimpleClusterPlan(logger.LoggerMixin):
    '''
    simple:

        template: cluster-simple.yml.j2

        head:
          hostname: 'head'
          image: 'centos7:ssh'

        compute:
          hostname:
              prefix: 'node'
              suffix_len: 3
          image:  'centos7:ssh'
    '''

    def __init__(self, cluster_network, plan_entries):
        self.cluster_network = cluster_network
        util.defensive_merge(plan_entries, self.__dict__)

    def create_blueprints(self):
        '''
        Creates an instance of SimpleClusterBlueprint
        '''
        cluster_specs = self.build_specs()
        self.logger.debug(cluster_specs)
        return SimpleClusterBlueprint(self.cluster_network, cluster_specs, self.template)

    def build_specs(self):
        '''
        Creates a dictionary of node specs that will be used for the cluster blueprint.

        A 'simple' cluster always has a single head, and zero or more compute nodes, depending
        on compute_count.

        Example output: for compute_count = 3, add a head node and 3 compute nodes:

        cluster_specs = {
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': PlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos7:ssh',
                    ip_address='172.30.0.253',
                    role='head'),
                '172.30.0.1': PlannedNode(
                    hostname='node001',
                    container='mycluster-node001',
                    image='centos7:ssh',
                    ip_address='172.30.0.1',
                    role='compute'),
                '172.30.0.2': PlannedNode(
                    hostname='node002',
                    container='mycluster-node002',
                    image='centos7:ssh',
                    ip_address='172.30.0.2',
                    role='compute'),
                '172.30.0.3': PlannedNode(
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
        head_ip = self.cluster_network.head_ip()
        head_hostname = self.head['hostname']
        head_image = self.head['image']

        # always have a head and a network
        head_entry = self.create_node_entry(self.name, head_hostname, head_ip,
                                            head_image, 'head')
        network_entry = self.cluster_network.as_dict()

        cluster_specs = {
            'name': self.name,
            'nodes': {
                head_ip: head_entry
            },
            'network': network_entry
        }

        # add compute nodes, should raise NetworkSubnetTooSmall if there are not enough IPs
        compute_ips = self.cluster_network.compute_ips(self.compute_count)
        compute_image = self.compute['image']

        for index, compute_ip in enumerate(compute_ips):

            compute_hostname = self.create_compute_hostname(index)
            node_entry = self.create_node_entry(self.name, compute_hostname,
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
        name_prefix = self.compute['hostname']['prefix']
        suffix_len = self.compute['hostname']['suffix_len']

        suffix_str = '{0:0%sd}' % str(suffix_len)
        suffix = suffix_str.format(index + 1)
        return name_prefix + suffix

    def create_node_entry(self, cluster_name, hostname, ip_address, image, role):
        '''
        Create an entry for node specs. The container name is inferred from the hostname.
        '''

        container_name = DockerNaming.create_container_name(cluster_name, hostname)

        return PlannedNode(hostname=hostname,
                           container=container_name,
                           image=image,
                           ip_address=ip_address,
                           role=role)

    def as_dict(self):
        '''
        Dictionary version of ClusterPlan
        '''
        interesting_keys = ('name', 'head', 'compute', 'template')
        d = util.defensive_subset(self.__dict__, interesting_keys)
        d['network'] = self.cluster_network.as_dict()
        return d

    @classmethod
    def create(cls, creation_request, simple_config, cluster_network):
        '''
        Build plan based on user request, existing configuration and a existing network.
        The parameters in the user request are merged with existing configuration.
        '''

        # keep merge simple for now
        plan_entries = util.defensive_merge(simple_config, creation_request._asdict())
        return SimpleClusterPlan(cluster_network, plan_entries)


class SimpleClusterBlueprint(logger.LoggerMixin):

    def __init__(self, cluster_network, cluster_specs, template):
        self.cluster_network = cluster_network
        self.cluster_specs = cluster_specs
        self.template = template

        # small initialization to have a list of nodes handy
        ordered_node_ips = sorted(cluster_specs['nodes'].keys())
        self.ordered_nodes = [
            cluster_specs['nodes'][ordered_ip]
            for ordered_ip
            in ordered_node_ips
        ]

    def deploy(self, renderer, deployer):

        cluster_definition = renderer.render_blueprint(self.as_dict(), self.template)
        deployer.deploy(cluster_definition)
        # deployed_cluster = cluster.from_docker(name)

        log_msg = 'Docker cluster %s -  %s created!'
        self.logger.info(log_msg % (self.name, self.cluster_network))

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

    def format(self, formatter):
        '''
        Format the cluster to some representation, e.g. as text.
        '''
        return formatter.format(self.as_dict())

    def as_dict(self):
        '''
        Dictionary version of SimpleClusterBlueprint
        '''
        return self.cluster_specs


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
