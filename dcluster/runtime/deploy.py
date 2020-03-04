import os

from runitmockit import runit

from dcluster.util import fs as fs_util
from dcluster.util import logger


class ComposeFailure(Exception):
    pass


class DockerComposeDeployer(logger.LoggerMixin):

    def __init__(self, compose_path):
        self.compose_path = compose_path

    def deploy(self, compose_definition):

        # save definition in file
        fs_util.create_dir_dont_complain(self.compose_path)
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
