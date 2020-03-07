'''
Utility functions for collections.
'''

import collections
import copy


def update_recursively(d, u):
    '''
    Updates the dictionary d with the contents of dictionary u.

    Will add new key/value pairs for every nested dictionary inside u that are not in d,
    essentially complementing the structure.

    If a key in u exists in d in the same place, the value is updated.
    '''
    # https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth

    # upgraded to python3-compatible code, seems OK
    if not u:
        return d

    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            # value is also a dictionary, apply recursion on nested dictionary.
            d[k] = update_recursively(d.get(k, {}), v)

        else:
            # either adds a key/value pair (when the value is not a dictionary),
            # or updates an existing key.
            d[k] = v

    return d


def defensive_copy(original_dict):
    '''
    Creates a copy of a dictionary that can be independently modified.
    Useful when using default cluster configuration (flavor) as a template for cluster instances,
    among other cases.
    '''
    return copy.deepcopy(original_dict)


def defensive_merge(source_dict, target_dict):
    '''
    Updates target_dict with source_dict, but it does not let target_dict be modified
    by subsequent modifications of source_dict elements.

    It also does not modify source_dict, uses defensive_copy.

    TODO use update_recursively?
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
    Subsets a dictionary with the keys that are not in the provided keys.
    The new dictionary is independent of the original.
    '''
    all_keys = set(source_dict.keys())
    remaining_keys = all_keys.difference(set(keys))
    return defensive_subset(source_dict, remaining_keys)
