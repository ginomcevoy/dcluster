#
# Some default values to interact with Docker
#

# Use this B-class network to create all subnet networks for Docker clusters
SUPERNET = '172.30.0.0/16'

# Use these amount of bits for each Docker cluster
CIDR_BITS = 24

CLUSTER_PREFS = {
    'HEAD_NAME': 'head',
    'GATEWAY_NAME': 'gateway',
    'COMPUTE_PREFIX': 'node',
    'COMPUTE_SUFFIX_LEN': 3,
    'NETWORK_PREFIX': 'dcluster'
}
