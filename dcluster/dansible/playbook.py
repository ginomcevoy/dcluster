import logging
import os

from runitmockit import runit


def execute_playbook(playbook_file, inventory_file, extra_vars=None):
    '''
    Run an Ansible playbook using a cluster as the inventory nodes.
    This will call 'ansible-playbook' command and print the output.
    '''
    # Ugly for now, until we add more functionality
    logger = logging.getLogger()
    extra_vars_str = ''
    if extra_vars is not None:
        extra_vars_str = '--extra-vars "%s"' % extra_vars

    (playbook_path, playbook_filename) = os.path.split(playbook_file)

    cmd = 'ansible-playbook -i %s %s %s' % (inventory_file, playbook_filename, extra_vars_str)
    cwd = playbook_path
    logger.debug('executing from %s >>%s<<' % (cwd, cmd))
    runit.execute(cmd, cwd=cwd, logger=logger, log_level=logging.INFO)
