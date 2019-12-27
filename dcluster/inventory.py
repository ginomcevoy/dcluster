'''
Create an Ansible inventory for a request of a Docker cluster.
'''

import os
import shutil
import yaml

from dcluster import ALL, CHILDREN, HOSTS, HOSTNAME, TYPE, NETWORK, CONTAINER
from config import dcluster_config


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
            '172.30.0.253': {
                'hostname': 'slurmctld',
                'container': 'mycluster-slurmctld',
                'type': 'head'
            },
            '172.30.0.1': {
                'hostname': 'node001',
                'container': 'mycluster-node001',
                'type': 'compute'
            },
            '172.30.0.2': {
                'hostname': 'node002',
                'container': 'mycluster-node002',
                'type': 'compute'
            },
            '172.30.0.3': {
                'hostname': 'node003',
                'container': 'mycluster-node003',
                'type': 'compute'
            }
        }
        and network_name, then creates an Ansible inventory in dictionary form:

        ---

        all:
            hosts:
                172.30.0.253:
                    hostname: slurmctld
                    container: mycluster-slurmctld
                172.30.0.1:
                    hostname: node001
                    container: mycluster-node001
                172.30.0.2:
                    hostname: node002
                    container: mycluster-node002
                172.30.0.3:
                    hostname: node003
                    container: mycluster-node003

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
                network_name: 'mycluster'
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
            self.inventory_dict[ALL][HOSTS][node_ip] = self.dict_for_host(node_dict)

            # check for new types
            t = node_dict[TYPE]
            self.add_type_if_needed(t)

            # add node to its type
            self.children[t][HOSTS][node_ip] = None

        return self.inventory_dict

    def dict_for_host(self, node_dict):
        d = {HOSTNAME: node_dict[HOSTNAME]}
        if CONTAINER in node_dict:
            # gateway is in inventory but does not have a container
            d[CONTAINER] = node_dict[CONTAINER]
        return d

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


class AnsibleEnvironment:

    def __init__(self, cluster_home, ansible_home, inventory):
        self.cluster_home = cluster_home
        self.ansible_home = ansible_home
        self.inventory = inventory

    @classmethod
    def create(cls, network_name, host_details, environment_home):
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

        cluster_home = os.path.join(environment_home, network_name)
        create_dir_dont_complain(cluster_home)

        # delete ansible if it exists, then create it again
        ansible_home = os.path.join(cluster_home, 'ansible')
        if os.path.isdir(ansible_home):
            shutil.rmtree(ansible_home)
        create_dir_dont_complain(ansible_home)

        # group_vars_dir = os.path.join(ansible_home, 'group_vars')
        # create_dir_dont_complain(group_vars_dir)

        # create inventory.yml
        inventory_file = os.path.join(ansible_home, 'inventory.yml')
        inventory = AnsibleInventory(network_name, host_details)
        inventory.to_yaml(inventory_file)

        # copy static files
        ansible_static_path = dcluster_config.get('ansible_static_path')
        copytree(ansible_static_path, ansible_home)

        return AnsibleEnvironment(cluster_home, ansible_home, inventory)


def create_dir_dont_complain(directory):
    try:
        os.makedirs(directory)
    except OSError:
        if not os.path.isdir(directory):
            raise


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


import unittest
from dcluster import networking
from six.moves import input


class DockerAnsibleIntegrationTest(unittest.TestCase):

    def test_create_docker_network_and_ansible_inventory(self):

        supernet = '172.31.0.0/16'
        cidr_bits = 24
        first_subnet = '172.31.1.0/24'
        network_name = 'mycluster'
        network_factory = networking.DockerClusterNetworkFactory(supernet, cidr_bits)

        print('*** test_create_docker_network_and_ansible_inventory ***')
        print('This test will use the main network %s' % supernet)
        print('About to create Docker network: %s = %s' % (network_name, str(first_subnet)))
        print('Make sure that this network does not exist in Docker!')
        input('Press Enter to continue')

        network = network_factory.create(network_name)
        host_details = network.build_host_details(3)

        basepath = '/tmp'
        AnsibleEnvironment.create(network_name, host_details, basepath)

        input('Created... press enter to remove docker network')
        network.remove()


if __name__ == '__main__':
    unittest.main()
