'''
Used when deploying using a package builder such as rpmbuild:

- create the production configuration
- install the production configuration to CONFIG_FILE (specified in root __init__.py)
- copy non-python artifacts (e.g. yml files) to their proper location within
  the path indicated by the DCLUSTER_INSTALL_PREFIX environment variable.
'''

# print to stderr - https://stackoverflow.com/a/14981125
from __future__ import print_function

import os
import shutil
import sys
import yaml

from dcluster import CONFIG_FILE
from dcluster.config import main_config
from dcluster.util import fs as fs_util


def install_production_config(sandbox_dir):
    '''
    Production environment is obtained by reading both config/common.yml and config/prod.yml
    '''

    # create from sources
    production_config = main_config.create_prod_config()

    (config_deploy_dir, config_deploy_filename) = os.path.split(CONFIG_FILE)

    # save to production config file, note the buildroot
    # join will not work, CONFIG_DIR is abs path
    sandboxed_config_dir = sandbox_dir + config_deploy_dir
    fs_util.create_dir_dont_complain(sandboxed_config_dir)

    # save YAML fle
    sandboxed_config_file = os.path.join(sandboxed_config_dir, config_deploy_filename)
    with open(sandboxed_config_file, 'w') as scf:
        # https://stackoverflow.com/a/47940875
        yaml.dump(production_config, scf, default_flow_style=False)

    return sandboxed_config_file


def root_source_dir():
    '''
    Calculate <dcluster_source> directory using the fact that it is one level above
    this module, outside the deployment package (deployment/deploy.py -> deployment/../)
    '''
    dir_of_this_module = fs_util.get_module_directory('deployment.deploy')
    return os.path.dirname(dir_of_this_module)


def install_source_artifact(artifact_relative_dir, sandboxed_target_dir):
    '''
    Copies a source artifact to the path specified in the deployed (production) configuration file
    Note that DCLUSTER_INSTALL_PREFIX should have been exported, so that the paths in the deployed
    configuration have already been prefixed by DCLUSTER_INSTALL_PREFIX.

    The sandboxed_target_dir should have the final directory, e.g.
    templates (artifact_relative_dir) -> /usr/share/dcluster/templates (sandboxed_target_dir)
    '''

    # find the artifact within dcluster source
    artifact_source = os.path.join(root_source_dir(), artifact_relative_dir)

    # copy the entire directory if target does not exist, assume it was done if target is present
    if not os.path.isdir(sandboxed_target_dir):
        shutil.copytree(artifact_source, sandboxed_target_dir)


def install_dcluster(sandbox_dir):

    # e.g. /etc/dcluster/config.yml
    sandboxed_config_file = install_production_config(sandbox_dir)

    # for debugging/testing purposes
    print(sandboxed_config_file)

    # install templates and ansible_static folders
    install_source_artifact('templates', main_config.paths('templates'))
    install_source_artifact('ansible_static', main_config.paths('ansible_static'))

    # install cluster flavors, note that the entry is a list
    # assuming the first element has the dcluster-supplied path
    install_source_artifact('config/flavors', main_config.paths('flavors')[0])


if __name__ == '__main__':

    # DCLUSTER_INSTALL_PREFIX is required for deployment, even if it is '/'
    if 'DCLUSTER_INSTALL_PREFIX' not in os.environ:
        print('Need to set DCLUSTER_INSTALL_PREFIX environment variable for deployment!',
              file=sys.stderr)
        print('Run "export DCLUSTER_INSTALL_PREFIX=/" to install directly to filesystem.',
              file=sys.stderr)
        exit(1)

    # If we are working within rpmbuild, we should get RPM_BUILD_ROOT
    sandbox_dir = os.environ['DCLUSTER_INSTALL_PREFIX']
    install_dcluster(sandbox_dir)
