import collections
import importlib
import os
import yaml
import sys


from dcluster import CONFIG_DIR, CONFIG_FILE


# Singleton for dcluster configuration
__dcluster_config = None


def get_module_filename(module_name):

    # if module not available, try to import it manually
    if module_name not in sys.modules:
        importlib.import_module(module_name)

    actual_module = sys.modules[module_name]
    return actual_module.__file__


def get_module_directory(module_name):
    module_filename = get_module_filename(module_name)
    return os.path.dirname(module_filename)


def dev_config_dir():
    dir_of_this_module = get_module_directory('dcluster.config')
    config_dir = os.path.join(os.path.dirname(dir_of_this_module), 'config')
    return config_dir


def read_config(config_dir, config_filename):

    config_file = os.path.join(config_dir, config_filename)
    config_dict = None
    with open(config_file, 'r') as cf:
        config_dict = yaml.load(cf)

    return config_dict


def update_recursively(d, u):
    # https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth

    # TODO unit test this, it was 'iteritmes' before, also there may be corner cases
    if not u:
        return d

    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = update_recursively(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def read_dev_config():
    '''
    Development environment is obtained by reading both config/common.yml and config/dev.yml
    '''
    config_dir = dev_config_dir()

    common_config = read_config(config_dir, 'common.yml')
    dev_config = read_config(config_dir, 'dev.yml')

    # we don't want to lose key/value pairs in subdictionaries
    update_recursively(common_config, dev_config)

    return common_config


def read_prod_config():
    return read_config(CONFIG_DIR, CONFIG_FILE)


def is_development():
    '''
    Read the presence of the environment variable
    '''
    return 'DCLUSTER_DEV' in os.environ


def get_config():
    global __dcluster_config
    if not __dcluster_config:

        # need to read configuration, use feature toggle to determine which to load
        if is_development():
            __dcluster_config = read_dev_config()
        else:
            __dcluster_config = read_prod_config()

    # defensive copying
    return dict(__dcluster_config)


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


def internal(key):
    '''
    Configuration sub-element for internals
    '''
    return get_config()['internal'][key]


if __name__ == '__main__':
    import pprint
    pprint.pprint(get_config())
