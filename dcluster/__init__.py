#
# Some default values to interact with Docker
#

# Use this B-class network to create all subnet networks for Docker clusters
SUPERNET = '172.30.0.0/16'

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
NETWORK = 'network_name'

#
# Constants for a Docker cluster
#
HEAD_NAME = 'slurmctld'
HEAD_TYPE = 'head'
COMPUTE_PREFIX = 'node'
COMPUTE_SUFFIX_LEN = 3
COMPUTE_TYPE = 'compute'
CONTAINER = 'container'
