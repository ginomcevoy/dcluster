'''
Utility functions for filesystem and paths.
'''
import importlib
import os
import sys


from runitmockit import runit


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


def evaluate_shell_path(path_str):
    '''
    Given a shell path (e.g. $HOME/.dcluster), returns the actual path, by calling a shell.
    NOTE: better to use os.path.expandvars!?
    '''
    # command_str = 'cd %s; pwd' % path_str # does not work if dir does not exist!
    command_str = 'readlink -f %s' % path_str
    result = runit.execute(command_str)
    real_path = result[0].strip()
    return real_path


if __name__ == '__main__':

    real_path = evaluate_shell_path('$HOME/.dcluster')
    print(real_path)

    real_path = evaluate_shell_path('$PWD')
    print(real_path)
