import os
import yaml

from dcluster import CONFIG_FILE

from dcluster.util import collection as collection_util
from dcluster.util import fs as fs_util


# Singleton for dcluster configuration
__dcluster_config = None


def read_config(config_dir, config_filename):
    '''
    Reads the configuration file, e.g. with YAML
    '''

    config_file = os.path.join(config_dir, config_filename)
    config_dict = None
    with open(config_file, 'r') as cf:
        config_dict = yaml.load(cf)

    return config_dict


def create_dev_config():
    '''
    Configuration for development environment is created by reading both
    config/common.yml and config/dev.yml and merging their contents to a single dictionary.
    '''
    config_dir = config_dir_from_source()

    common_config = read_config(config_dir, 'common.yml')
    dev_only_config = read_config(config_dir, 'dev.yml')

    # we don't want to lose key/value pairs in subdictionaries
    return collection_util.update_recursively(common_config, dev_only_config)


def create_prod_config():
    '''
    Configuration for development environment is created by reading both
    config/common.yml and config/prod.yml and merging their contents to a single dictionary.
    '''
    config_dir = config_dir_from_source()

    common_config = read_config(config_dir, 'common.yml')
    prod_only_config = read_config(config_dir, 'prod.yml')

    # we don't want to lose key/value pairs in subdictionaries
    return collection_util.update_recursively(common_config, prod_only_config)


def read_deployed_config(config_source, dcluster_install_prefix):
    '''
    Configuration from a deployed source, e.g. /etc/dcluster/config.yml
    The paths may be prefixed by dcluster_install_prefix
    '''

    (config_dir, config_filename) = os.path.split(config_source)

    if dcluster_install_prefix:
        # prefix configuration path
        config_dir = dcluster_install_prefix + config_dir

    deployed_config = read_config(config_dir, config_filename)

    if dcluster_install_prefix and 'paths' in deployed_config:

        # prefix paths with the supplied root

        # note that this is only done when running dcluster inside a prefixed directory
        # paths in the production configuration will not be affected by this change.

        # TODO handle cases where this should not be done, e.g. $HOME, if need arises
        for entry, one_or_more_paths in deployed_config['paths'].items():

            # handle lists
            if isinstance(one_or_more_paths, list):

                # entry in paths is a list
                deployed_config['paths'][entry] = [
                    dcluster_install_prefix + item_path
                    for item_path
                    in one_or_more_paths
                ]
            else:
                # just one path in the entry
                deployed_config['paths'][entry] = dcluster_install_prefix + one_or_more_paths

    return deployed_config


def config_dir_from_source():
    '''
    Calculate <dcluster_source>/config directory using the fact that it is one level above
    this module, outside the dcluster package
    (dcluster/config/main_config.py -> dcluster/../config)
    '''
    dir_of_this_module = fs_util.get_module_directory('dcluster.config')
    dcluster_dir = os.path.dirname(os.path.dirname(dir_of_this_module))
    return os.path.join(dcluster_dir, 'config')


def get_config():
    '''
    Read the configuration from a file.
    Uses a singleton pattern (since many calls to get_config() are done within a request).

    Also detects whether to use development configuration or special prefixed deployment
    configuration, using environment variables.
    '''
    global __dcluster_config
    if not __dcluster_config:

        # need to read configuration, use feature toggle to determine which to load
        if 'DCLUSTER_DEV' in os.environ:
            # override to use development config from source code
            __dcluster_config = create_dev_config()

        elif 'DCLUSTER_INSTALL_PREFIX' in os.environ:
            # override the root of production dcluster configuration (default is '/')
            # useful when doing rpmbuild testing
            __dcluster_config = read_deployed_config(CONFIG_FILE,
                                                     os.environ['DCLUSTER_INSTALL_PREFIX'])

        else:
            # use the config file that dcluster is expected to have deployed (after installing RPM)
            __dcluster_config = read_deployed_config(CONFIG_FILE, None)

    return __dcluster_config


def networking(key):
    '''
    Configuration sub-element for networking.
    '''
    return get_config()['networking'][key]


def naming(key):
    '''
    Configuration sub-element for naming.
    '''
    return get_config()['naming'][key]


def prefs(key):
    '''
    Configuration sub-element for various preferences.
    '''
    return get_config()['prefs'][key]


def paths(key):
    '''
    Configuration sub-element for paths. These paths may be prefixed by dcluster_install_prefix.
    '''

    one_or_more_paths = get_config()['paths'][key]

    # handle lists
    if isinstance(one_or_more_paths, list):
        return [
            os.path.expanduser(os.path.expandvars(a_path))
            for a_path
            in one_or_more_paths
        ]
    else:
        return os.path.expanduser(os.path.expandvars(one_or_more_paths))


def composer_workpath(cluster_name):
    '''
    Where to store the composer output.
    '''
    workpath = paths('work')
    return os.path.join(workpath, 'clusters', cluster_name)


def inventory_workpath(cluster_name):
    '''
    Where to store the Ansible inventory for a cluster.
    '''
    return composer_workpath(cluster_name)


def default_inventory(cluster_name):
    iw = inventory_workpath(cluster_name)
    return os.path.join(iw, 'inventory.yml')


def playbook_workpath(cluster_name):
    '''
    Where to store Ansible playbook directories.
    '''
    workpath = paths('work')
    return os.path.join(workpath, 'ansible')


if __name__ == '__main__':
    import pprint
    print('*** ALL ***')
    pprint.pprint(get_config())
    pprint.pprint(paths('work'))
