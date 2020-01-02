'''
Used when creating the RPM:

- create the production configuration
'''

import os
import shutil
import sys
import yaml

from dcluster import CONFIG_FILE
from dcluster import config, util


def create_production_config(sandbox_dir):
    '''
    Development environment is obtained by reading both config/common.yml and config/dev.yml
    '''

    # create from sources
    production_config = config.create_prod_config()

    (config_deploy_dir, config_deploy_filename) = os.path.split(CONFIG_FILE)

    # save to production config file, note the buildroot
    # join will not work, CONFIG_DIR is abs path
    sandboxed_config_dir = sandbox_dir + config_deploy_dir
    util.create_dir_dont_complain(sandboxed_config_dir)

    sandboxed_config_file = os.path.join(sandboxed_config_dir, config_deploy_filename)

    with open(sandboxed_config_file, 'w') as scf:
        # https://stackoverflow.com/a/47940875
        yaml.dump(production_config, scf, default_flow_style=False)

    return sandboxed_config_file


def templates_dir_from_source():
    '''
    Calculate <dcluster_source>/templates directory using the fact that it is one level above
    this module, outside the deployment package (deployment/deploy.py -> deployment/../templates)
    '''
    dir_of_this_module = util.get_module_directory('deployment.deploy')
    return os.path.join(os.path.dirname(dir_of_this_module), 'templates')


def copy_templates(sandbox_dir):
    '''
    Copy templates to the path specified in the production configuration file
    Note that this means that the path should not be prefixed here
    (don't call this script with DCLUSTER_ROOT!)
    '''
    # read templates from here
    template_source = templates_dir_from_source()

    # where the production template will be at build time (the paths are also sandboxed...)
    production_config_at_sandbox = config.get_config(dcluster_root=sandbox_dir)
    production_template_dir = production_config_at_sandbox['paths']['templates']

    # copy the entire directory (assumes that the production target ends with 'templates')
    # don't copy anything if the target dir exists, assume it was already done
    if not os.path.isdir(production_template_dir):
        shutil.copytree(template_source, production_template_dir)


if __name__ == '__main__':
    # Assuming we are working within rpmbuild, we get RPM_BUILD_ROOT
    sandbox_dir = sys.argv[1]
    sandboxed_config_file = create_production_config(sandbox_dir)
    copy_templates(sandbox_dir)

    # this can be picked up by the external build process, e.g. for testing (?)
    print(sandboxed_config_file)
