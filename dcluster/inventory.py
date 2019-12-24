'''
Create an Ansible inventory for a request of a Docker cluster.
'''

import yaml

from dcluster import ALL, CHILDREN, HOSTS, HOSTNAME, TYPE


class AnsibleInventory:
    '''
    Creates an Ansible YAML file given a dictionary:

    host_details = {
        '172.30.0.253': {'hostname': 'slurmctld', 'type': 'head'},
        '172.30.0.1': {'hostname': 'node001', 'type': 'compute'},
        '172.30.0.2': {'hostname': 'node002', 'type': 'compute'},
        '172.30.0.3': {'hostname': 'node003', 'type': 'compute'},
    }
    '''

    def __init__(self, host_details):
        self.host_details = host_details
        self.inventory_dict = None

    def create_dict(self):
        '''
        Function that takes the following dictionary:

        host_details = {
            '172.30.0.253': {'hostname': 'slurmctld', 'type': 'head'},
            '172.30.0.1': {'hostname': 'node001', 'type': 'compute'},
            '172.30.0.2': {'hostname': 'node002', 'type': 'compute'},
            '172.30.0.3': {'hostname': 'node003', 'type': 'compute'},
        }

        and creates an Ansible inventory in dictionary form:

        ---

        all:
            hosts:
                172.30.0.253:
                    hostname: slurmctld
                172.30.0.1:
                    hostname: node001
                172.30.0.2:
                    hostname: node002
                172.30.0.3:
                    hostname: node003

            children:
                head:
                    hosts:
                        172.30.0.253:
                compute:
                    hosts:
                        172.30.0.1:
                        172.30.0.2:
                        172.30.0.3:
        '''
        self.inventory_dict = {ALL: {HOSTS: {}, CHILDREN: {}}}
        self.children = self.inventory_dict[ALL][CHILDREN]

        for node_ip, node_dict in self.host_details.items():

            # add node to hosts
            self.inventory_dict[ALL][HOSTS][node_ip] = {HOSTNAME: node_dict['hostname']}

            # check for new types
            t = node_dict[TYPE]
            self.add_type_if_needed(t)

            # add node to its type
            self.children[t][HOSTS][node_ip] = None

        return self.inventory_dict

    def add_type_if_needed(self, t):
        if t not in self.children:
            self.children[t] = {HOSTS: {}}

    def to_yaml(self, filename):
        if self.inventory_dict is None:
            self.create_dict()

        with open(filename, 'w') as file:
            # https://stackoverflow.com/a/47940875
            yaml.dump(self.inventory_dict, file, default_flow_style=False)

        return filename
