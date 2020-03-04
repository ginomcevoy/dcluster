from .blueprint import ClusterBlueprint

from dcluster.util import collection as collection_util
from dcluster.util import logger

from dcluster.node.planner import SimpleNodePlanner, ExtendedNodePlanner


def simple_plan_data(simple_config, creation_request):
    # keep merge simple for now
    return collection_util.defensive_merge(simple_config, creation_request._asdict())


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
        self.plan_data = collection_util.defensive_copy(plan_data)
        self.node_planner = node_planner

    def create_blueprints(self):
        '''
        Creates an instance of ClusterBlueprint
        '''
        cluster_specs = self.build_specs()
        self.logger.debug(cluster_specs)
        return ClusterBlueprint(self.cluster_network, cluster_specs)

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

        # head_plan = self.create_node_plan(self.name, head_hostname, head_ip,
        #                                     head_image, 'head')

        # # begin from existing entries, include head node spec
        # # this allows keeping 'extra' entries in the plan
        # undesired_keys = ('head', 'compute', 'compute_count')
        # cluster_specs = collection_util.defensive_subtraction(self.plan_entries, undesired_keys)

        # # always have a head and the network
        # cluster_specs['network'] = self.cluster_network.as_dict()
        # cluster_specs['nodes'] = {head_ip: head_plan}

        # # add compute nodes, should raise NetworkSubnetTooSmall if there are not enough IPs
        # compute_ips = self.cluster_network.compute_ips(self.compute_count)
        # compute_image = self.compute['image']

        # for index, compute_ip in enumerate(compute_ips):

        #     compute_hostname = self.create_compute_hostname(index)
        #     node_plan = self.create_node_plan(self.name, compute_hostname,
        #                                         compute_ip, compute_image, 'compute')
        #     cluster_specs['nodes'][compute_ip] = node_plan

        # return cluster_specs

        plan_data = self.plan_data
        cluster_network = self.cluster_network
        node_planner = self.node_planner

        # initialize with name, template, network
        cluster_specs = collection_util.defensive_subset(plan_data, ('flavor', 'name', 'template'))
        cluster_specs['network'] = cluster_network.as_dict()

        # always have a head
        head_plan = node_planner.create_head_plan(plan_data)
        cluster_specs['nodes'] = {head_plan.ip_address: head_plan}

        # create <compute_count> nodes
        compute_ips = cluster_network.compute_ips(plan_data['compute_count'])
        for index, compute_ip in enumerate(compute_ips):
            compute_plan = node_planner.create_compute_plan(plan_data, index, compute_ip)
            cluster_specs['nodes'][compute_plan.ip_address] = compute_plan

        return cluster_specs

    def as_dict(self):
        '''
        Dictionary version of ClusterPlan
        '''
        interesting_keys = ('name', 'head', 'compute', 'template')
        d = collection_util.defensive_subset(self.plan_data, interesting_keys)
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


class ExtendedClusterPlan(SimpleClusterPlan):
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

    def build_specs(self):
        # build the 'simple' specs, noting that the ExtendedNodePlanner will be used
        simple_cluster_specs = super(ExtendedClusterPlan, self).build_specs()

        # the specs are missing the docker volumes at the bottom.
        # For now just get the docker volumes from the head role
        # TODO add volumes from other roles (compute) when we have a proper test
        docker_volumes_head = self.plan_data['head']['docker_volumes']

        volumes_entry = [
            docker_volume[0:docker_volume.find(':')]
            for docker_volume
            in docker_volumes_head
        ]
        simple_cluster_specs['volumes'] = volumes_entry

        return simple_cluster_specs

    @classmethod
    def create(cls, creation_request, extended_config, cluster_network):
        '''
        Build plan based on user request, existing configuration and a existing network.
        The parameters in the user request are merged with existing configuration.
        '''
        plan_data = simple_plan_data(extended_config, creation_request)
        node_planner = ExtendedNodePlanner(cluster_network)
        return ExtendedClusterPlan(cluster_network, plan_data, node_planner)
