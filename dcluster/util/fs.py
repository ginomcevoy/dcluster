'''
Utility functions for filesystem and paths.
'''
import importlib
import os
import shutil
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


def copytree(src, dst, symlinks=False, ignore=None):
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


if __name__ == '__main__':

    real_path = evaluate_shell_path('$HOME/.dcluster')
    print(real_path)

    real_path = evaluate_shell_path('$PWD')
    print(real_path)
