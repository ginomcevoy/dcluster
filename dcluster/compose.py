import os
import jinja2
import logging

from runitmockit import runit

from . import CLUSTER_PREFS


class ComposeFailure(Exception):
    pass


class ClusterComposer(object):

    def __init__(self, compose_path, templates_dir, cluster_prefs=CLUSTER_PREFS):
        self.compose_path = compose_path
        self.templates_dir = templates_dir
        self.cluster_prefs = cluster_prefs

        self.log = logging.getLogger()

    def build_definition(self, cluster_specs, template_filename):

        # build the replacement dictionary
        replacements = dict(**cluster_specs)
        replacements['CLUSTER_PREFS'] = self.cluster_prefs
        self.log.debug(replacements)

        # Load Jinja2 template
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(self.templates_dir),
                                 trim_blocks=True, lstrip_blocks=True)
        template = env.get_template(template_filename)
        compose_definition = template.render(**replacements)
        self.log.debug(compose_definition)
        return compose_definition

    def compose(self, compose_definition):

        # save definition in file
        create_dir_dont_complain(self.compose_path)
        definition_file = os.path.join(self.compose_path, 'docker-cluster.yml')
        with open(definition_file, 'w') as df:
            df.write(compose_definition)

        # call docker-compose command, should pick up the created file
        # note: apparently, using docker-compose.yml and removing '-f' fails to
        # to acknowledge the --force-recreate option
        cmd = 'docker-compose --no-ansi -f docker-cluster.yml up -d --force-recreate'
        run = runit.execute(cmd, cwd=self.compose_path)
        print(run[1])

        if run[2]:
            raise ComposeFailure('docker-compose command failed, check output')


def create_dir_dont_complain(directory):
    try:
        os.makedirs(directory)
    except OSError:
        if not os.path.isdir(directory):
            raise
