import os

from dcluster.util import logger

from . import main_config


def inventory_workpath(cluster_name):
    '''
    Where to store the Ansible inventory for a cluster.
    '''
    return main_config.composer_workpath(cluster_name)


def default_inventory(cluster_name):
    iw = inventory_workpath(cluster_name)
    return os.path.join(iw, 'inventory.yml')


def installed_playbook_path():
    '''
    Where to store Ansible playbook directories.
    '''
    workpath = main_config.paths('work')
    return os.path.join(workpath, 'dansible')


def default_playbook_path():
    return main_config.paths('ansible_static')


def find_playbook_path(playbook_name):
    '''
    Finds the path for a dansible playbook given a name.
    The path is one of the following:

    1. a subdirectory of the current user directory, i.e. $PWD/<playbook_name>
    2. a subdirectory of the 'installed' dansible playbooks, e.g. $HOME/.dcluster/dansible/<playbook_name>
    3. a subdirectory of the 'default' dansible playbooks, e.g.
          /usr/share/dcluster/ansible_static/<playbook_name>

    These paths are in order of precedence: the first subdirectory is chosen if it exists,
    if not try the second and so on.

    The path *must* contain the playbook as "playbook.yml" (not checked here)

    Raises ValueError if no directory containing the playbook_name is found.
    '''
    log = logger.logger_for_me(find_playbook_path)

    # the three paths that may contain the subdirectory
    places_to_look = [
        os.getcwd(),
        installed_playbook_path(),
        default_playbook_path()
    ]

    found_playbook_path = None

    for place_to_look in places_to_look:
        possible_path = os.path.join(place_to_look, playbook_name)
        if os.path.isdir(possible_path):
            found_playbook_path = possible_path
            break

    if not found_playbook_path:
        raise ValueError('Could not find {} directory in any of these places: {}'.format(playbook_name, places_to_look))

    log.debug('Found playbook path: {}'.format(found_playbook_path))

    return found_playbook_path


if __name__ == '__main__':
    import sys
    print(find_playbook_path(sys.argv[1]))
