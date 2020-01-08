from . import simple

from dcluster import dyaml
from dcluster.plan import ExtendedPlannedNode


class ExtendedNodePlanner(simple.SimpleNodePlanner):
    '''
    Creates extended node entries for the ClusterBlueprint (cluster_specs dictionary).
    The entries can include Docker volumes (both docker-specific and filesystem binds), and
    a chunk of 'static' text that is added to the specification without parsing, but with the
    proper indentation for a later renderization.
    '''

    def create_head_plan(self, plan_data):
        simple_planned_head = super(ExtendedNodePlanner, self).create_head_plan(plan_data)
        return self.extend_plan(plan_data, simple_planned_head)

    def create_compute_plan(self, plan_data, index, compute_ip):
        simple_planned_compute = super(ExtendedNodePlanner, self).create_compute_plan(plan_data,
                                                                                      index,
                                                                                      compute_ip)
        return self.extend_plan(plan_data, simple_planned_compute)

    def extend_plan(self, plan_data, simple_planned_node):
        role = simple_planned_node.role

        # join the two type of volumes
        volumes = list(plan_data[role]['shared_volumes'])
        volumes.extend(plan_data[role]['docker_volumes'])

        # the static text needs to be indented to show up properly
        static_without_offset = plan_data[role]['static']
        static_text = dyaml.dump_with_offset_indent(static_without_offset, 4)

        # reuse simple plan and add to it
        extended_dict = simple_planned_node._asdict()
        extended_dict['volumes'] = volumes
        extended_dict['static_text'] = static_text
        return ExtendedPlannedNode(**extended_dict)


class ExtendedClusterPlan(simple.SimpleClusterPlan):
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

        plan_data = simple.simple_plan_data(extended_config, creation_request)
        node_planner = ExtendedNodePlanner(cluster_network)
        return ExtendedClusterPlan(cluster_network, plan_data, node_planner)
