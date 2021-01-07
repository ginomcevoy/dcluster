'''
Create an Ansible inventory for a request of a Docker cluster.
'''

import yaml

from dcluster.util import collection as collection_util


class AnsibleInventory:
    '''
    Creates an Ansible YAML file given the cluster specification (ClusterBlueprint).
    See create_dict() for the expected output.
    '''

    def __init__(self, cluster_specs):
        self.cluster_specs = cluster_specs
        self.inventory_dict = None

    def create_dict(self):
        '''
        Function that takes the following dictionary:

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
                'subnet': '172.30.0.0'
                'address': '172.30.0.0/24',
                'gateway': 'gateway',
                'gateway_ip': '172.30.0.254'
            },
            'template': 'cluster-basic.yml.j2'
        }
        then creates an Ansible inventory in dictionary form:

        ---

        all:
            hosts:
                172.30.0.253:
                    hostname: head
                    container: mycluster-head
                    image: centos7:ssh
                    ip_address: 172.30.0.253
                172.30.0.1:
                    hostname: node001
                    container: mycluster-node001
                    image: centos7:ssh
                    ip_address: 172.30.0.1
                172.30.0.2:
                    hostname: node002
                    container: mycluster-node002
                    image: centos7:ssh
                    ip_address: 172.30.0.2
                172.30.0.3:
                    hostname: node003
                    container: mycluster-node003
                    image: centos7:ssh
                    ip_address: 172.30.0.3
            children:
                head:
                    hosts:
                        172.30.0.253:
                compute:
                    hosts:
                        172.30.0.1:
                        172.30.0.2:
                        172.30.0.3:

            vars:
                cluster_flavor: basic
                cluster_name: mycluster
                cluster_network:
                    address: 172.30.0.0/24
                    subnet: 172.30.0.0
                    prefix: 24
                    netmask: 255.255.255.0
                    broadcast: 172.30.0.255
                    gateway: gateway
                    gateway_ip: 172.30.0.254
                    name: dcluster-mycluster
                cluster_template: cluster-basic.yml.j2

        The IP addresses are used instead of the hostnames, because the hostnames are not expected
        to be resolvable by the host (gateway). However, the names will be resolvable within the
        cluster.
        '''
        self.inventory_dict = {
            'all': {
                'hosts': {},
                'children': {},
                'vars': {
                    'cluster_flavor': self.cluster_specs['flavor'],
                    'cluster_name': self.cluster_specs['name'],
                    'cluster_network': self.cluster_specs['network'],
                    'cluster_template': self.cluster_specs['template']
                }
            }
        }
        self.children = self.inventory_dict['all']['children']

        for node_ip, planned_node in self.cluster_specs['nodes'].items():

            # add node to hosts
            self.inventory_dict['all']['hosts'][node_ip] = self.dict_for_node(planned_node)

            # check for new groups
            self.add_group_if_needed(planned_node.role)

            # add node to its type
            self.children[planned_node.role]['hosts'][node_ip] = None

        return self.inventory_dict

    def dict_for_node(self, planned_node):
        '''
        Returns a dictionary that represents the data of a node inside the inventory.
        The node may contain additional information that is not required for this inventory,
        e.g. Docker volumes, these are left out.
        '''
        keys = ('hostname', 'container', 'image', 'ip_address')
        return collection_util.defensive_subset(planned_node._asdict(), keys)

    def add_group_if_needed(self, role):
        '''
        Insert a new child for the 'children' dictionary (Ansible group).
        Ansible groups match cluster roles.
        '''
        if role not in self.children:
            self.children[role] = {'hosts': {}}

    def to_yaml(self, filename):
        '''
        Saves the inventory as a YAML file.
        '''
        if self.inventory_dict is None:
            self.create_dict()

        with open(filename, 'w') as file:
            # https://stackoverflow.com/a/47940875
            yaml.dump(self.inventory_dict, file, default_flow_style=False)

        return filename
