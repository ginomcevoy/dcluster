from collections import OrderedDict
import os
import yaml

from . import main_config

from dcluster.util import collection as collection_util
from dcluster.util import fs
from dcluster.util import logger as log_util

# read profiles only once
__all_profiles__ = None


def all_available_profiles(user_places_to_look=None):
    '''
    Singleton pattern for available profiles.
    '''
    global __all_profiles__
    if __all_profiles__ is None:
        __all_profiles__ = get_all_available_profiles(user_places_to_look)
    return __all_profiles__


def get_all_available_profiles(user_places_to_look):
    '''
    Finds the YAML files with cluster information.
    The YAML files *must* have one of the following items:

    - it is a dictionary of exactly one key/value pair
    - the value is a dictionary, the key will be the profile identifier
    - either the items 'cluster_type' OR 'extend' should be in the internal dictionary
      (having both is allowed)

    TODO
    - enforce restrictions?
    '''
    logger = log_util.logger_for_me(get_all_available_profiles)
    candidate_yaml_files = find_candidate_yaml_files(user_places_to_look)

    # here we overwrite any repeated yaml file without consideration of where they were found
    profile_yaml_files = []
    for location, candidates in candidate_yaml_files.items():
        for candidate in candidates:
            profile_yaml_path = os.path.join(location, candidate)
            profile_yaml_files.append(profile_yaml_path)

    available_profiles = OrderedDict()
    for profile_file in profile_yaml_files:

        with open(profile_file, 'r') as ff:
            yaml_dict = yaml.load(ff, Loader=yaml.SafeLoader)

            # inform the user if a profile is to be updated
            for profile_name in yaml_dict.keys():
                if profile_name in available_profiles:
                    log_msg = 'profile \"{}\" will be updated with definition at: {}'
                    logger.info(log_msg.format(profile_name, profile_file))

            # a YAML file may have many profiles, this will add all of them
            # allow override of previously defined profiles
            available_profiles.update(yaml_dict)

    logger.debug('Found profiles: {}'.format(list(available_profiles.keys())))

    return available_profiles


def find_candidate_yaml_files(user_places_to_look=None):
    '''
    Finds YAML files in the specified paths. Allows the user to pass custom directories.
    '''
    logger = log_util.logger_for_me(find_candidate_yaml_files)

    # look in default places
    dcluster_places_to_look = main_config.paths('profiles')
    places_to_look = collection_util.defensive_copy(dcluster_places_to_look)

    # also include user-specified places
    if user_places_to_look is not None and isinstance(user_places_to_look, list):
        places_to_look.extend(user_places_to_look)

    logger.debug('places to look for profiles: {}'.format(places_to_look))

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


def cluster_config_for_profile(profile, user_places_to_look=None):
    '''
    Cluster properties given its profile name.
    '''
    available_profiles = all_available_profiles(user_places_to_look)
    cluster_config = available_profiles[profile]

    # if the requested profile extends another, recursively extend
    if 'extend' in cluster_config.keys():

        # stop self-references
        if profile == cluster_config['extend']:
            raise ValueError('Self reference found for profile {}!'.format(profile))

        # really bad if a more complex circular reference exists
        parent_profile = cluster_config['extend']
        parent_config = cluster_config_for_profile(parent_profile)
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

    default_profile_files = find_candidate_yaml_files(None)
    print('profile files: %s' % str(default_profile_files))

    default_profiles = all_available_profiles(None)
    print('============\n')
    print('raw profiles:')

    import pprint
    for profile_name, profile_dict in default_profiles.items():
        print(profile_name)
        pprint.pprint(profile_dict)

    print('============\n')
    print('complete profiles:')
    for profile_name in default_profiles.keys():
        complete_profile_config = cluster_config_for_profile(profile_name)
        print(profile_name)
        pprint.pprint(complete_profile_config)
