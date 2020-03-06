from collections import namedtuple


# information expected from the user when building a 'basic' cluster
BasicCreationRequest = namedtuple('BasicCreationRequest', ['name', 'compute_count', 'flavor'])
