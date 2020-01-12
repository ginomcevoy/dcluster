import os
import yaml


from dcluster import CONFIG_FILE
from dcluster.util import collection as collection_util
from dcluster.util import fs as fs_util


# Singleton for dcluster configuration
__dcluster_config = None


def read_config(config_dir, config_filename):

    config_file = os.path.join(config_dir, config_filename)
    config_dict = None
    with open(config_file, 'r') as cf:
        config_dict = yaml.load(cf)

    return config_dict


def create_dev_config():
    '''
    Configuration for development environment is created by reading both
    config/common.yml and config/prod.yml
    '''
    config_dir = config_dir_from_source()

    common_config = read_config(config_dir, 'common.yml')
    dev_only_config = read_config(config_dir, 'dev.yml')

    # we don't want to lose key/value pairs in subdictionaries
    return collection_util.update_recursively(common_config, dev_only_config)


def create_prod_config():
    '''
    Configuration for production environment is created by reading both
    config/common.yml and config/prod.yml
    '''
    config_dir = config_dir_from_source()

    common_config = read_config(config_dir, 'common.yml')
    dev_only_config = read_config(config_dir, 'prod.yml')

    # we don't want to lose key/value pairs in subdictionaries
    return collection_util.update_recursively(common_config, dev_only_config)


def read_deployed_config(config_source, dcluster_root):
    '''
    Configuration from a deployed source, e.g. /etc/dcluster/config.yml
    The paths may be prefixed by dcluster_root
    '''

    (config_dir, config_filename) = os.path.split(config_source)

    if dcluster_root:
        # prefix configuration path
        config_dir = dcluster_root + config_dir

    deployed_config = read_config(config_dir, config_filename)

    if dcluster_root and 'paths' in deployed_config:
        # prefix paths with the supplied root
        for entry, value in deployed_config['paths'].items():
            deployed_config['paths'][entry] = dcluster_root + deployed_config['paths'][entry]

    return deployed_config


def config_dir_from_source():
    '''
    Calculate <dcluster_source>/config directory using the fact that it is one level above
    this module, outside the dcluster package (dcluster/config.py -> dcluster/../config)
    '''
    dir_of_this_module = fs_util.get_module_directory('dcluster.config')
    return os.path.join(os.path.dirname(dir_of_this_module), 'config')


def get_config():
    global __dcluster_config
    if not __dcluster_config:

        # need to read configuration, use feature toggle to determine which to load
        if 'DCLUSTER_DEV' in os.environ:
            # override to use development config from source code
            __dcluster_config = create_dev_config()

        elif 'DCLUSTER_ROOT' in os.environ:
            # override the root of production dcluster configuration (default is '/')
            # useful when doing rpmbuild testing
            __dcluster_config = read_deployed_config(CONFIG_FILE, os.environ['DCLUSTER_ROOT'])

        else:
            # use the config file that dcluster is expected to have deployed (after installing RPM)
            __dcluster_config = read_deployed_config(CONFIG_FILE, None)

    return __dcluster_config


def networking(key):
    '''
    Configuration sub-element for networking
    '''
    return get_config()['networking'][key]


def naming(key):
    '''
    Configuration sub-element for naming
    '''
    return get_config()['naming'][key]


def prefs(key):
    '''
    Configuration sub-element for various preferences
    '''
    return get_config()['prefs'][key]


def paths(key):
    '''
    Configuration sub-element for paths. These paths may be prefixed by dcluster_root.
    '''
    return os.path.expandvars(get_config()['paths'][key])


def for_cluster(key):
    '''
    Configuration sub-element for cluster properties.
    '''
    # read YAML
    cluster_config = get_config()['clusters'][key]

    # check if the cluster config extends another
    if 'extend' in cluster_config:

        # read the parent, but don't modify it!
        parent_config = get_config()['clusters'][cluster_config['extend']]
        parent_config = collection_util.defensive_copy(parent_config)

        # merge parent with current config
        cluster_config = collection_util.update_recursively(parent_config, cluster_config)

        # no need anymore
        del cluster_config['extend']

    return cluster_config


if __name__ == '__main__':
    import pprint
    print('*** ALL ***')
    pprint.pprint(get_config())
    pprint.pprint(paths('work'))

    print('*** SIMPLE ***')
    pprint.pprint(for_cluster('simple'))

    print('*** SLURM ***')
    pprint.pprint(for_cluster('slurm'))
