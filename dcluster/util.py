'''
Useful misc functions
'''

import collections
import importlib
import os
import sys


def update_recursively(d, u):
    # https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth

    # upgraded to python3-compatible code, seems OK
    if not u:
        return d

    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = update_recursively(d.get(k, {}), v)
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
