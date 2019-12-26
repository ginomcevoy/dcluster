'''
Create an Ansible inventory for a request of a Docker cluster.
'''

import os
import yaml

from dcluster import ALL, CHILDREN, HOSTS, HOSTNAME, TYPE, NETWORK


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

    def __init__(self, network_name, host_details):
        self.network_name = network_name
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
        and network_name, then creates an Ansible inventory in dictionary form:

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

            vars:
                network_name: 'cluster'
        '''
        self.inventory_dict = {
            ALL: {
                HOSTS: {},
                CHILDREN: {},
                'vars': {
                    NETWORK: self.network_name
                }
            }
        }
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

    @classmethod
    def create_structure(cls, network_name, host_details, environment_home):
        '''
        Creates the necessary Ansible files to manage a (container) cluster.
        This comprises the following structure:
        |- <environment_home>
            |- <cluster_name>
                |- ansible
                    |- inventory.yml
        - inventory.yml is created by AnsibleInventory.
        '''
        # create all directories
        create_dir_dont_complain(environment_home)

        cluster_dir = os.path.join(environment_home, network_name)
        create_dir_dont_complain(cluster_dir)

        ansible_dir = os.path.join(cluster_dir, 'ansible')
        create_dir_dont_complain(ansible_dir)

        # group_vars_dir = os.path.join(ansible_dir, 'group_vars')
        # create_dir_dont_complain(group_vars_dir)

        # create inventory.yml
        inventory_file = os.path.join(ansible_dir, 'inventory.yml')
        inventory = AnsibleInventory(network_name, host_details)
        inventory.to_yaml(inventory_file)
        return inventory


def create_dir_dont_complain(directory):
    try:
        os.makedirs(directory)
    except OSError:
        if not os.path.isdir(directory):
            raise


import unittest
from dcluster import networking
from six.moves import input


class DockerAnsibleIntegrationTest(unittest.TestCase):

    def test_create_docker_network_and_ansible_inventory(self):

        supernet = '172.31.0.0/16'
        cidr_bits = 24
        first_subnet = '172.31.0.0/24'
        network_name = 'ansible-docker-example'
        network_factory = networking.DockerClusterNetworkFactory(supernet, cidr_bits)

        print('*** test_create_docker_network_and_ansible_inventory ***')
        print('This test will use the main network %s' % supernet)
        print('About to create Docker network: %s = %s' % (network_name, str(first_subnet)))
        print('Make sure that this network does not exist in Docker!')
        input('Press Enter to continue')

        network = network_factory.create(network_name)
        host_details = network.build_host_details(3)

        basepath = '/tmp'
        AnsibleInventory.create_structure(network_name, host_details, basepath)

        input('Created... press enter to remove docker network')
        network.remove()


if __name__ == '__main__':
    unittest.main()
