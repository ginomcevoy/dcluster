'''
Create an Ansible inventory for a request of a Docker cluster.
'''

import yaml

from dcluster.util import collection as collection_util


class AnsibleInventory:
    '''
    Creates an Ansible YAML file given the cluster specification (ClusterBlueprint).
    '''

    def __init__(self, cluster_specs):
        self.cluster_specs = cluster_specs
        self.inventory_dict = None

    def create_dict(self):
        '''
        Function that takes the following dictionary:

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
        then creates an Ansible inventory in dictionary form:

        ---

        all:
            hosts:
                172.30.0.253:
                    hostname: head
                    container: mycluster-head
                    image: centos7:ssh
                172.30.0.1:
                    hostname: node001
                    container: mycluster-node001
                    image: centos7:ssh
                172.30.0.2:
                    hostname: node002
                    container: mycluster-node002
                    image: centos7:ssh
                172.30.0.3:
                    hostname: node003
                    container: mycluster-node003
                    image: centos7:ssh
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
                cluster_flavor: simple
                cluster_name: mycluster
                cluster_network:
                    address: 172.30.0.0/24
                    gateway: gateway
                    gateway_ip: 172.30.0.254
                    name: mycluster
                cluster_template: cluster-simple.yml.j2

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

            # check for new roles
            self.add_role_if_needed(planned_node.role)

            # add node to its type
            self.children[planned_node.role]['hosts'][node_ip] = None

        return self.inventory_dict

    def dict_for_node(self, planned_node):
        keys = ('hostname', 'container', 'image')
        return collection_util.defensive_subset(planned_node._asdict(), keys)

    def add_role_if_needed(self, role):
        if role not in self.children:
            self.children[role] = {'hosts': {}}

    def to_yaml(self, filename):
        if self.inventory_dict is None:
            self.create_dict()

        with open(filename, 'w') as file:
            # https://stackoverflow.com/a/47940875
            yaml.dump(self.inventory_dict, file, default_flow_style=False)

        return filename
