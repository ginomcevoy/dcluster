import os

from .inventory import AnsibleInventory
from .playbook import execute_playbook

from dcluster.config import dansible_config
from dcluster.util import fs as fs_util


def create_inventory(cluster_specs, inventory_workpath):
    fs_util.create_dir_dont_complain(inventory_workpath)
    ansible_inventory = AnsibleInventory(cluster_specs)

    inventory_file = os.path.join(inventory_workpath, 'inventory.yml')
    ansible_inventory.to_yaml(inventory_file)
    return (ansible_inventory, inventory_file)


def run_playbook(cluster_name, playbook_name, inventory_file, extra_vars=None):

    # find our playbook: it is inside a directory <playbook_name> in some paths, see dansible_config
    playbook_path = dansible_config.find_playbook_path(playbook_name)

    # 'install' the playbook in dcluster working directory, oif it wasn't there already
    dansible_home = dansible_config.installed_playbook_path()
    playbook_target = os.path.join(dansible_home, playbook_name)

    if playbook_path != playbook_target:
        fs_util.create_dir_dont_complain(playbook_target)
        fs_util.copytree(playbook_path, playbook_target)

    # always run from working directory
    playbook_filename = 'playbook.yml'
    playbook_file = os.path.join(playbook_target, playbook_filename)
    execute_playbook(playbook_file, inventory_file, extra_vars)
