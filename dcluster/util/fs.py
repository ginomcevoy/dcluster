'''
Utility functions for filesystem and paths.
'''

import importlib
import os
import shutil
import sys


from . import runit


def get_module_filename(module_name):
    '''
    Given a Python module, returns the full path where its source code is located.
    '''

    # if module not available, try to import it manually
    if module_name not in sys.modules:
        importlib.import_module(module_name)

    actual_module = sys.modules[module_name]
    return actual_module.__file__


def get_module_directory(module_name):
    '''
    Given a Python module, returns the directory where its source code is located.
    '''
    module_filename = get_module_filename(module_name)
    return os.path.dirname(module_filename)


def create_dir_dont_complain(directory):
    '''
    Create a directory structure, stay silent if the directory exists.
    '''
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


def copytree(src, dst, symlinks=False, ignore=None):
    '''
    Copies path/to/src/* to path/to/dst/, recursively.
    '''
    # try:
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.exists(d):
            if os.path.isdir(d):
                shutil.rmtree(d)
            else:
                os.remove(d)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)
    # except FileExistsError:
        # pass


def find_files_with_extension(dirpath, extension):
    '''
    list all files in directory (not-recursive) that have an extension, e.g. '.txt'
    '''
    # only for actual dirs
    files = []

    if os.path.isdir(dirpath):
        files = [
            file
            for file in os.listdir(dirpath)
            if file.endswith(extension)
        ]

    return files


def check_directories_exist(directories):
    '''
    Fails if one directory in the list does not exist.
    '''
    for directory in directories:
        if not os.path.isdir(directory):
            raise OSError('Directory does not exist: {}'.format(directory))


if __name__ == '__main__':

    real_path = evaluate_shell_path('$HOME/.dcluster')
    print(real_path)

    real_path = evaluate_shell_path('$PWD')
    print(real_path)

    # find config/profiles with YAML files
    dir_of_this_module = get_module_directory('dcluster.util.fs')
    dcluster_dir = os.path.dirname(os.path.dirname(dir_of_this_module))
    profile_dir = os.path.join(dcluster_dir, 'config/profiles')

    # find YAML files there
    yaml_files = find_files_with_extension(profile_dir, '.yml')
    print('profile files: %s' % str(yaml_files))

    # attempt to find where there are none (here)
    no_files = find_files_with_extension(dir_of_this_module, '.yml')
    print('no files here: %s' % str(no_files))
