from . import BasicPlannedNode, DefaultPlannedNode

from dcluster.infra.docker_facade import DockerNaming
from dcluster.util import dyaml


class BasicNodePlanner(object):
    '''
    Basic class for DefaultNodePlanner, used to describe a container from information retrieved
    from Docker, after the default cluster has been instantiated.
    '''

    def __init__(self, cluster_network):
        self.cluster_network = cluster_network

    def create_head_plan(self, plan_data):
        '''
        Creates an instance of BasicPlannedNode for the head of the cluster.
        '''
        head_ip = self.cluster_network.head_ip()
        head_hostname = plan_data['head']['hostname']
        head_image = plan_data['head']['image']

        head_plan = self.create_node_plan(plan_data['name'], head_hostname, head_ip,
                                          head_image, 'head')

        return head_plan

    def create_compute_plan(self, plan_data, index, compute_ip):
        '''
        Creates an instance of BasicPlannedNode for one of the compute nodes in the cluster.
        '''
        compute_hostname = self.create_compute_hostname(plan_data, index)
        compute_image = plan_data['compute']['image']
        compute_plan = self.create_node_plan(plan_data['name'], compute_hostname, compute_ip,
                                             compute_image, 'compute')
        return compute_plan

    def create_node_plan(self, cluster_name, hostname, ip_address, image, role):
        '''
        Creates an instance of BasicPlannedNode for some node of the cluster.
        '''
        container_name = DockerNaming.create_container_name(cluster_name, hostname)
        return BasicPlannedNode(hostname, container_name, image, ip_address, role)

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


class DefaultNodePlanner(BasicNodePlanner):
    '''
    Creates node entries for the ClusterBlueprint (cluster_specs dictionary).
    Requires a cluster plan that already has all the necessary information (config + request)
    to design the cluster specifications.

    The entries can include Docker volumes (both docker-specific and filesystem binds), and
    a chunk of 'static' text that is added to the specification without parsing, but with the
    proper indentation for a later renderization.
    '''
    def __init__(self, cluster_network):
        super(DefaultNodePlanner, self).__init__(cluster_network)
        self.basic = super(DefaultNodePlanner, self)

    def create_head_plan(self, plan_data):
        '''
        Creates an instance of DefaultNodePlanner for the head of the cluster.
        '''
        # reuse BasicPlannedNode for the basic details
        basic_planned_head = self.basic.create_head_plan(plan_data)
        return self.extend_plan(plan_data, basic_planned_head)

    def create_compute_plan(self, plan_data, index, compute_ip):
        '''
        Creates an instance of DefaultNodePlanner for the head of the cluster.
        '''
        # reuse BasicPlannedNode for the basic details
        basic_planned_compute = self.basic.create_compute_plan(plan_data, index, compute_ip)
        return self.extend_plan(plan_data, basic_planned_compute)

    def extend_plan(self, plan_data, basic_planned_node):
        '''
        Promotes an instance of BasicNodePlanner to DefaultNodePlanner, by adding more details.
        '''
        role = basic_planned_node.role

        # join the two type of volumes
        volumes = []
        if 'shared_volumes' in plan_data[role]:
            volumes.extend(plan_data[role]['shared_volumes'])
        if 'docker_volumes' in plan_data[role]:
            volumes.extend(plan_data[role]['docker_volumes'])

        # the static text needs to be indented to show up properly
        static_text = ''
        if 'static' in plan_data[role]:
            static_without_offset = plan_data[role]['static']
            static_text = dyaml.dump_with_offset_indent(static_without_offset, 4)

        # reuse basic plan and add to it
        extended_dict = basic_planned_node._asdict()
        extended_dict['volumes'] = volumes
        extended_dict['static_text'] = static_text

        # will container run systemctl?
        extended_dict['systemctl'] = False
        if plan_data[role].get('systemctl', False):
            extended_dict['systemctl'] = True

        return DefaultPlannedNode(**extended_dict)
