import logging
import os

from runitmockit import runit


def execute_playbook(playbook_file, inventory_file, extra_vars_list=[]):
    '''
    Run an Ansible playbook using a cluster as the inventory nodes.
    This will call 'ansible-playbook' command and print the output.
    '''
    logger = logging.getLogger()

    # the playbook will be run from the user's current directory, this ensures that files
    # passed at extra-vars will be found
    cwd = os.path.abspath(os.getcwd())

    # build extra-vars as-is, supports a list (subsequent calls)
    extra_vars_str = ''
    for extra_vars in extra_vars_list:
        extra_vars_str = '--extra-vars "%s"' % extra_vars

    # (playbook_path, playbook_filename) = os.path.split(playbook_file)

    cmd = 'ansible-playbook -i %s %s %s' % (inventory_file, playbook_file, extra_vars_str)
    # cwd = playbook_path
    logger.debug('executing from %s >>%s<<' % (cwd, cmd))
    runit.execute(cmd, cwd=cwd, logger=logger, log_level=logging.INFO)
