from . import SimplePlannedNode, ExtendedPlannedNode

from dcluster.infra.docker_facade import DockerNaming
from dcluster.util import dyaml


class SimpleNodePlanner(object):
    '''
    Creates node entries for the ClusterBlueprint (cluster_specs dictionary).
    Requires a cluster plan that already has all the necessary information (config + request)
    to design the cluster specifications.
    '''
    def __init__(self, cluster_network):
        self.cluster_network = cluster_network

    def create_head_plan(self, plan_data):
        head_ip = self.cluster_network.head_ip()
        head_hostname = plan_data['head']['hostname']
        head_image = plan_data['head']['image']

        head_plan = self.create_node_plan(plan_data['name'], head_hostname, head_ip,
                                          head_image, 'head')

        return head_plan

    def create_compute_plan(self, plan_data, index, compute_ip):
        compute_hostname = self.create_compute_hostname(plan_data, index)
        compute_image = plan_data['compute']['image']
        compute_plan = self.create_node_plan(plan_data['name'], compute_hostname, compute_ip,
                                             compute_image, 'compute')
        return compute_plan

    def create_node_plan(self, cluster_name, hostname, ip_address, image, role):
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


class ExtendedNodePlanner(SimpleNodePlanner):
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
