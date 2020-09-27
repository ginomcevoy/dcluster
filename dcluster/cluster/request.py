from collections import namedtuple


# information expected from the user when building a 'default' cluster
DefaultCreationRequest = namedtuple('DefaultCreationRequest',
                                    ['name', 'compute_count', 'flavor', 'flavor_paths',
                                    'playbooks', 'extra_vars_list'])
