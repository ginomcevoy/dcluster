import os
import yaml

from . import main_config

from dcluster.util import collection as collection_util
from dcluster.util import fs


def get_all_available_flavors(user_places_to_look=None):
    '''
    Finds the YAML files with cluster information.
    The YAML files *must* have one of the following items:

    - it is a dictionary of exactly one key/value pair
    - the value is a dictionary, the key will be the flavor identifier
    - either the items 'cluster_type' OR 'extend' should be in the internal dictionary
      (having both is allowed)

    TODO
    - enforce restrictions
    - allow more entries in file
    - handle collisions: user-specified places have priority

    '''
    candidate_yaml_files = find_candidate_yaml_files(user_places_to_look)

    # TODO enforce restrictions and handle collisions
    flavor_yaml_files = []
    for location, candidates in candidate_yaml_files.items():
        for candidate in candidates:
            flavor_yaml_path = os.path.join(location, candidate)
            flavor_yaml_files.append(flavor_yaml_path)

    available_flavors = {}
    for flavor_file in flavor_yaml_files:

        with open(flavor_file, 'r') as ff:
            yaml_dict = yaml.load(ff)

            # TODO more flavors, for now only getting the first
            flavor_name = list(yaml_dict)[0]
            available_flavors[flavor_name] = yaml_dict[flavor_name]

    return available_flavors


def find_candidate_yaml_files(user_places_to_look=None):
    '''
    Finds YAML files in the specified paths
    '''

    # look in default places
    dcluster_places_to_look = main_config.paths('flavors')
    places_to_look = collection_util.defensive_copy(dcluster_places_to_look)

    # also include user-specified places
    if user_places_to_look is not None and isinstance(user_places_to_look, list):
        places_to_look.extend(user_places_to_look)

    # find all the yaml files, remember found place
    yaml_files = {}
    for place_to_look in places_to_look:
        with_yml = fs.find_files_with_extension(place_to_look, '.yml')
        with_yaml = fs.find_files_with_extension(place_to_look, '.yaml')
        yaml_files[place_to_look] = []
        yaml_files[place_to_look].extend(with_yml)
        yaml_files[place_to_look].extend(with_yaml)

    return yaml_files


def cluster_config_for_flavor(flavor, user_places_to_look=None):
    '''
    Cluster properties given its flavor name.
    '''

    available_flavors = get_all_available_flavors(user_places_to_look)
    cluster_config = available_flavors[flavor]

    # if the requested flavor extends another, recursively extend
    if 'extend' in cluster_config.keys():

        # really bad if circular references
        parent_flavor = cluster_config['extend']
        parent_config = cluster_config_for_flavor(parent_flavor)
        parent_config = collection_util.defensive_copy(parent_config)

        # merge parent with current config
        cluster_config = collection_util.update_recursively(parent_config, cluster_config)

        # no need for this
        del cluster_config['extend']

    return cluster_config


# def for_cluster(key):
#     '''
#     Configuration sub-element for cluster properties.
#     '''
#     # read YAML
#     cluster_config = get_config()['clusters'][key]

#     # check if the cluster config extends another
#     if 'extend' in cluster_config:

#         # read the parent, but don't modify it!
#         parent_config = get_config()['clusters'][cluster_config['extend']]
#         parent_config = collection_util.defensive_copy(parent_config)

#         # merge parent with current config
#         cluster_config = collection_util.update_recursively(parent_config, cluster_config)

#         # no need anymore
#         del cluster_config['extend']

#     return cluster_config

if __name__ == '__main__':
    default_flavor_files = find_candidate_yaml_files(None)
    print('flavor files: %s' % str(default_flavor_files))

    default_flavors = get_all_available_flavors(None)
    print('============\n')
    print('raw flavors:')

    import pprint
    for flavor_name, flavor_dict in default_flavors.items():
        print(flavor_name)
        pprint.pprint(flavor_dict)

    print('============\n')
    print('complete flavors:')
    for flavor_name in default_flavors.keys():
        complete_flavor_config = cluster_config_for_flavor(flavor_name)
        print(flavor_name)
        pprint.pprint(complete_flavor_config)
