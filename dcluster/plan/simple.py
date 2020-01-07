from operator import attrgetter

from dcluster import logger, util
from dcluster.docker_facade import DockerNaming

from . import SimplePlannedNode


def simple_plan_data(simple_config, creation_request):
    # keep merge simple for now
    return util.defensive_merge(simple_config, creation_request._asdict())


class SimpleNodePlanner(object):

    def __init__(self, cluster_network):
        self.cluster_network = cluster_network

    def create_head_entry(self, plan_data):
        head_ip = self.cluster_network.head_ip()
        head_hostname = plan_data['head']['hostname']
        head_image = plan_data['head']['image']

        head_entry = self.create_node_entry(plan_data['name'], head_hostname, head_ip,
                                            head_image, 'head')

        return head_entry

    def create_compute_entry(self, plan_data, index, compute_ip):
        compute_hostname = self.create_compute_hostname(plan_data, index)
        compute_image = plan_data['compute']['image']
        compute_entry = self.create_node_entry(plan_data['name'], compute_hostname, compute_ip,
                                               compute_image, 'compute')
        return compute_entry

    def create_node_entry(self, cluster_name, hostname, ip_address, image, role):
        container_name = self.create_container_name(cluster_name, hostname)
        return SimplePlannedNode(hostname, container_name, image, ip_address, role)

    def create_container_name(self, cluster_name, hostname):
        return DockerNaming.create_container_name(cluster_name, hostname)

    def create_compute_hostname(self, plan_data, index):
        '''
        Returns the hostname of a compute node given its index.

        Ex.
        0 -> node001
        1 -> node002
        '''
        name_prefix = plan_data['compute']['hostname']['prefix']
        suffix_len = plan_data['compute']['hostname']['suffix_len']

        suffix_str = '{0:0%sd}' % str(suffix_len)
        suffix = suffix_str.format(index + 1)
        return name_prefix + suffix


class SimpleClusterPlan(logger.LoggerMixin):
    '''
    as_dict= {
        'name': 'test',
        'head': {
            'hostname': 'head',
            'image': 'centos7:ssh'
        },
        'compute': {
            'hostname': {
                'prefix': 'node',
                'suffix_len': 3
            },
            'image': 'centos7:ssh'
        },
        'network': cluster_network.as_dict(),
        'template': 'cluster-simple.yml.j2'
    }
    '''

    def __init__(self, cluster_network, plan_data, node_planner):
        self.cluster_network = cluster_network
        self.plan_data = util.defensive_copy(plan_data)
        self.node_planner = node_planner

    def create_blueprints(self):
        '''
        Creates an instance of SimpleClusterBlueprint
        '''
        cluster_specs = self.build_specs()
        self.logger.debug(cluster_specs)
        return SimpleClusterBlueprint(self.cluster_network, cluster_specs)

    def build_specs(self):
        '''
        Creates a dictionary of node specs that will be used for the cluster blueprint.

        A 'simple' cluster always has a single head, and zero or more compute nodes, depending
        on compute_count.

        Example output: for compute_count = 3, add a head node and 3 compute nodes:

        cluster_specs = {
            'flavor': 'simple',
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': SimplePlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos7:ssh',
                    ip_address='172.30.0.253',
                    role='head'),
                '172.30.0.1': SimplePlannedNode(
                    hostname='node001',
                    container='mycluster-node001',
                    image='centos7:ssh',
                    ip_address='172.30.0.1',
                    role='compute'),
                '172.30.0.2': SimplePlannedNode(
                    hostname='node002',
                    container='mycluster-node002',
                    image='centos7:ssh',
                    ip_address='172.30.0.2',
                    role='compute'),
                '172.30.0.3': SimplePlannedNode(
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
            },
            'template': 'cluster-simple.yml.j2'
        }
        '''
        # head_ip = self.cluster_network.head_ip()
        # head_hostname = self.head['hostname']
        # head_image = self.head['image']

        # head_entry = self.create_node_entry(self.name, head_hostname, head_ip,
        #                                     head_image, 'head')

        # # begin from existing entries, include head node spec
        # # this allows keeping 'extra' entries in the plan
        # undesired_keys = ('head', 'compute', 'compute_count')
        # cluster_specs = util.defensive_subtraction(self.plan_entries, undesired_keys)

        # # always have a head and the network
        # cluster_specs['network'] = self.cluster_network.as_dict()
        # cluster_specs['nodes'] = {head_ip: head_entry}

        # # add compute nodes, should raise NetworkSubnetTooSmall if there are not enough IPs
        # compute_ips = self.cluster_network.compute_ips(self.compute_count)
        # compute_image = self.compute['image']

        # for index, compute_ip in enumerate(compute_ips):

        #     compute_hostname = self.create_compute_hostname(index)
        #     node_entry = self.create_node_entry(self.name, compute_hostname,
        #                                         compute_ip, compute_image, 'compute')
        #     cluster_specs['nodes'][compute_ip] = node_entry

        # return cluster_specs

        plan_data = self.plan_data
        cluster_network = self.cluster_network
        node_planner = self.node_planner

        # initialize with name, template, network
        cluster_specs = util.defensive_subset(plan_data, ('flavor', 'name', 'template'))
        cluster_specs['network'] = cluster_network.as_dict()

        # always have a head
        head_entry = node_planner.create_head_entry(plan_data)
        cluster_specs['nodes'] = {head_entry.ip_address: head_entry}

        # create <compute_count> nodes
        compute_ips = cluster_network.compute_ips(plan_data['compute_count'])
        for index, compute_ip in enumerate(compute_ips):
            compute_entry = node_planner.create_compute_entry(plan_data, index, compute_ip)
            cluster_specs['nodes'][compute_entry.ip_address] = compute_entry

        return cluster_specs

    def as_dict(self):
        '''
        Dictionary version of ClusterPlan
        '''
        interesting_keys = ('name', 'head', 'compute', 'template')
        d = util.defensive_subset(self.plan_data, interesting_keys)
        d['network'] = self.cluster_network.as_dict()
        return d

    @classmethod
    def create(cls, creation_request, simple_config, cluster_network):
        '''
        Build plan based on user request, existing configuration and a existing network.
        The parameters in the user request are merged with existing configuration.
        '''

        plan_data = simple_plan_data(simple_config, creation_request)
        node_planner = SimpleNodePlanner(cluster_network)
        return SimpleClusterPlan(cluster_network, plan_data, node_planner)


class SimpleClusterBlueprint(logger.LoggerMixin):

    def __init__(self, cluster_network, cluster_specs):
        self.cluster_network = cluster_network
        self.cluster_specs = cluster_specs

        # small initialization to have a list of nodes handy
        ordered_node_ips = sorted(cluster_specs['nodes'].keys())
        self.ordered_nodes = [
            cluster_specs['nodes'][ordered_ip]
            for ordered_ip
            in ordered_node_ips
        ]

    def deploy(self, renderer, deployer):
        template = self.cluster_specs['template']
        cluster_definition = renderer.render_blueprint(self.as_dict(), template)
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
