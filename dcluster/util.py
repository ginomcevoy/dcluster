'''
Useful misc functions
'''

import copy
import collections
import importlib
import os
import sys


def update_recursively(d, u, unique={}):
    # https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth

    # upgraded to python3-compatible code, seems OK
    if not u:
        return d

    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = update_recursively(d.get(k, {}), v, unique)

        else:
            d[k] = v

    return d


def get_module_filename(module_name):

    # if module not available, try to import it manually
    if module_name not in sys.modules:
        importlib.import_module(module_name)

    actual_module = sys.modules[module_name]
    return actual_module.__file__


def get_module_directory(module_name):
    module_filename = get_module_filename(module_name)
    return os.path.dirname(module_filename)


def create_dir_dont_complain(directory):
    try:
        os.makedirs(directory)
    except OSError:
        if not os.path.isdir(directory):
            raise


def defensive_copy(original_dict):
    return copy.deepcopy(original_dict)


def defensive_merge(source_dict, target_dict):
    '''
    Updates target_dict with source_dict, but it does not let target_dict be modified
    by later modifications of source_dict elements. It also does not modify source_dict.
    Uses defensive_copy.
    '''
    source_copy = defensive_copy(source_dict)
    target_dict.update(source_copy)
    return target_dict


def defensive_subset(source_dict, keys):
    '''
    Subsets a dictionary with the given keys. The new dictionary is independent of the original.
    '''
    subset = {key: source_dict[key] for key in keys if key in source_dict}
    return defensive_copy(subset)


def defensive_subtraction(source_dict, keys):
    '''
    Subsets a dictionary with the keys that are not in keys.
    The new dictionary is independent of the original.
    '''
    all_keys = set(source_dict.keys())
    remaining_keys = all_keys.difference(set(keys))
    return defensive_subset(source_dict, remaining_keys)
