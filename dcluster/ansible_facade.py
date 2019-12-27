
import logging

from runitmockit import runit


def run_playbook(playbook, cwd, extra_vars=None):
    '''
    Ugly for now...
    '''
    logger = logging.getLogger()
    extra_vars_str = ''
    if extra_vars is not None:
        extra_vars_str = '--extra-vars %s' % extra_vars
    cmd = 'ansible-playbook -i inventory.yml playbooks/%s %s' % (playbook, extra_vars_str)
    print('executing: %s' % cmd)
    runit.execute(cmd, cwd=cwd, logger=logger, log_level=logging.DEBUG)
