#
# Some default values to interact with Docker
#

# Use this B-class network to create all subnet networks for Docker clusters
MAIN_NETWORK = '172.30.0.0/16'

# Use these amount of bits for each Docker cluster
CIDR_BITS = 24


#
# Constants for Ansible inventory
#
ALL = 'all'
CHILDREN = 'children'
HOSTS = 'hosts'
HOSTNAME = 'hostname'
TYPE = 'type'
