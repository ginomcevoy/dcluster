from collections import OrderedDict
import os
import yaml

from . import main_config

from dcluster.util import collection as collection_util
from dcluster.util import fs
from dcluster.util import logger as log_util

# read flavors only once
__all_flavors__ = None


def all_available_flavors(user_places_to_look=None):
    '''
    Singleton pattern for available flavors.
    '''
    global __all_flavors__
    if __all_flavors__ is None:
        __all_flavors__ = get_all_available_flavors(user_places_to_look)
    return __all_flavors__


def get_all_available_flavors(user_places_to_look):
    '''
    Finds the YAML files with cluster information.
    The YAML files *must* have one of the following items:

    - it is a dictionary of exactly one key/value pair
    - the value is a dictionary, the key will be the flavor identifier
    - either the items 'cluster_type' OR 'extend' should be in the internal dictionary
      (having both is allowed)

    TODO
    - enforce restrictions?
    '''
    logger = log_util.logger_for_me(get_all_available_flavors)
    candidate_yaml_files = find_candidate_yaml_files(user_places_to_look)

    # here we overwrite any repeated yaml file without consideration of where they were found
    flavor_yaml_files = []
    for location, candidates in candidate_yaml_files.items():
        for candidate in candidates:
            flavor_yaml_path = os.path.join(location, candidate)
            flavor_yaml_files.append(flavor_yaml_path)

    available_flavors = OrderedDict()
    for flavor_file in flavor_yaml_files:

        with open(flavor_file, 'r') as ff:
            yaml_dict = yaml.load(ff)

            # inform the user if a flavor is to be updated
            for flavor_name in yaml_dict.keys():
                if flavor_name in available_flavors:
                    log_msg = 'Flavor \"{}\" will be updated with definition at: {}'
                    logger.info(log_msg.format(flavor_name, flavor_file))

            # a YAML file may have many flavors, this will add all of them
            # allow override of previously defined flavors
            available_flavors.update(yaml_dict)

    logger.debug('Found flavors: {}'.format(list(available_flavors.keys())))

    return available_flavors


def find_candidate_yaml_files(user_places_to_look=None):
    '''
    Finds YAML files in the specified paths. Allows the user to pass custom directories.
    '''
    logger = log_util.logger_for_me(find_candidate_yaml_files)

    # look in default places
    dcluster_places_to_look = main_config.paths('flavors')
    places_to_look = collection_util.defensive_copy(dcluster_places_to_look)

    # also include user-specified places
    if user_places_to_look is not None and isinstance(user_places_to_look, list):
        places_to_look.extend(user_places_to_look)

    logger.debug('places to look for flavors: {}'.format(places_to_look))

    # convert '~' to user's home directory
    places_to_look = [
        os.path.expanduser(place_to_look)
        for place_to_look
        in places_to_look
    ]

    # find all the yaml files, remember found place
    yaml_files = OrderedDict()
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
    available_flavors = all_available_flavors(user_places_to_look)
    cluster_config = available_flavors[flavor]

    # if the requested flavor extends another, recursively extend
    if 'extend' in cluster_config.keys():

        # stop self-references
        if flavor == cluster_config['extend']:
            raise ValueError('Self reference found for flavor {}!'.format(flavor))

        # really bad if a more complex circular reference exists
        parent_flavor = cluster_config['extend']
        parent_config = cluster_config_for_flavor(parent_flavor)
        parent_config = collection_util.defensive_copy(parent_config)

        # merge parent with current config
        cluster_config = collection_util.update_recursively(parent_config, cluster_config)

        # no need for this anymore
        del cluster_config['extend']

    return cluster_config


if __name__ == '__main__':
    import logging
    log_level = getattr(logging, 'DEBUG')
    logging.basicConfig(format='%(asctime)s - %(levelname)6s | %(message)s',
                        level=log_level, datefmt='%d-%b-%y %H:%M:%S')

    default_flavor_files = find_candidate_yaml_files(None)
    print('flavor files: %s' % str(default_flavor_files))

    default_flavors = all_available_flavors(None)
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
