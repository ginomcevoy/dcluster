from .blueprint import ClusterBlueprint

from dcluster.util import collection as collection_util
from dcluster.util import logger

from dcluster.node.planner import BasicNodePlanner, ExtendedNodePlanner


def basic_plan_data(basic_config, creation_request):
    '''
    Build a plan for creating a basic cluster.
    This is achieved by merging default dcluster configuration in the 'basic' flavor
    with user-supplied information, e.g. the name of the cluster, etc
    '''
    # keep merge simplified for now
    return collection_util.defensive_merge(basic_config, creation_request._asdict())


class BasicClusterPlan(logger.LoggerMixin):
    '''
    A place to build and realize the plan for a cluster.
    The strategy is to build a dictionary with all the available details of the cluster,
    and to create a ClusterBlueprint instance that will actually deploy the cluster.

    This plan assumes that the 'basic' template will be used, along with cluster flavors that are
    marked with the 'basic' type.

    The tasks of building the plan and deploying the clusters are kept in different classes,
    in order to reutilize blueprint code for clusters already deployed and retrieved later, while
    at the same time not including the code for building a cluster.

    Here follows an example of the plan_data that is received at input:

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
        'template': 'cluster-basic.yml.j2'
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

        A 'basic' cluster always has a single head, and zero or more compute nodes, depending
        on compute_count.

        Example output: for compute_count = 3, add a head node and 3 compute nodes:

        cluster_specs = {
            'flavor': 'basic',
            'name': 'mycluster',
            'nodes': {
                '172.30.0.253': BasicPlannedNode(
                    hostname='head',
                    container='mycluster-head',
                    image='centos7:ssh',
                    ip_address='172.30.0.253',
                    role='head'),
                '172.30.0.1': BasicPlannedNode(
                    hostname='node001',
                    container='mycluster-node001',
                    image='centos7:ssh',
                    ip_address='172.30.0.1',
                    role='compute'),
                '172.30.0.2': BasicPlannedNode(
                    hostname='node002',
                    container='mycluster-node002',
                    image='centos7:ssh',
                    ip_address='172.30.0.2',
                    role='compute'),
                '172.30.0.3': BasicPlannedNode(
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
            'template': 'cluster-basic.yml.j2'
        }
        '''
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
    def create(cls, creation_request, basic_config, cluster_network):
        '''
        Build plan based on user request, existing configuration and a existing network.
        The parameters in the user request are merged with existing configuration.
        '''

        plan_data = basic_plan_data(basic_config, creation_request)
        node_planner = BasicNodePlanner(cluster_network)
        return BasicClusterPlan(cluster_network, plan_data, node_planner)


class ExtendedClusterPlan(BasicClusterPlan):
    '''
    Similar to BasicClusterPlan, but here we assume that the 'extended' template will be used,
    along with cluster flavors that are marked with the 'extended' type.

    Here follows an example of the plan_data that is received at input:

    as_dict= {
        'name': 'test',
        'head': {
            'hostname': 'head',
            'image': 'centos7:ssh'
            'docker_volumes': ...
            'shared_volumes': ...
        },
        'compute': {
            'hostname': {
                'prefix': 'node',
                'suffix_len': 3
            },
            'image': 'centos7:ssh'
            'docker_volumes': ...
            'shared_volumes': ...
        },
        'volumes': ...
        'network': cluster_network.as_dict(),
        'template': 'cluster-extended.yml.j2'
    }
    '''

    def build_specs(self):
        '''
        Creates a dictionary of node specs that will be used for the cluster blueprint.

        An 'extended' cluster is similar to a 'basic' cluster, but also handles docker volumes.
        '''
        # build the 'basic' specs, noting that the ExtendedNodePlanner will be used
        basic_cluster_specs = super(ExtendedClusterPlan, self).build_specs()

        # the specs are missing the docker volumes at the bottom.
        # For now just get the docker volumes from the head role
        # TODO add volumes from other roles (compute) when we have a proper test
        docker_volumes_head = self.plan_data['head']['docker_volumes']

        volumes_entry = [
            docker_volume[0:docker_volume.find(':')]
            for docker_volume
            in docker_volumes_head
        ]
        basic_cluster_specs['volumes'] = volumes_entry

        return basic_cluster_specs

    @classmethod
    def create(cls, creation_request, extended_config, cluster_network):
        '''
        Build plan based on user request, existing configuration and a existing network.
        The parameters in the user request are merged with existing configuration.
        '''
        plan_data = basic_plan_data(extended_config, creation_request)
        node_planner = ExtendedNodePlanner(cluster_network)
        return ExtendedClusterPlan(cluster_network, plan_data, node_planner)
