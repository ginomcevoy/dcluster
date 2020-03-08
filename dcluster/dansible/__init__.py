import os

from .inventory import AnsibleInventory
from .playbook import execute_playbook

from dcluster.config import main_config
from dcluster.util import fs as fs_util


def create_inventory(cluster_specs, inventory_workpath):
    fs_util.create_dir_dont_complain(inventory_workpath)
    ansible_inventory = AnsibleInventory(cluster_specs)

    inventory_file = os.path.join(inventory_workpath, 'inventory.yml')
    ansible_inventory.to_yaml(inventory_file)
    return (ansible_inventory, inventory_file)


def run_playbook(cluster_name, playbook_name, inventory_file, extra_vars=None):
    # copy from ansible_static
    ansible_static_path = main_config.paths('ansible_static')
    playbook_path = os.path.join(ansible_static_path, playbook_name)

    ansible_home = main_config.playbook_workpath(cluster_name)
    playbook_target = os.path.join(ansible_home, playbook_name)
    fs_util.create_dir_dont_complain(playbook_target)
    fs_util.copytree(playbook_path, playbook_target)

    playbook_filename = playbook_name + '-playbook.yml'
    playbook_file = os.path.join(playbook_target, playbook_filename)
    execute_playbook(playbook_file, inventory_file, extra_vars)
