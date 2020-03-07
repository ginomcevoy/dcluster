import os

from runitmockit import runit

from dcluster.util import fs as fs_util
from dcluster.util import logger


class ComposeFailure(Exception):
    '''
    Raised when the deployment fails.
    '''
    pass


class DockerComposeDeployer(logger.LoggerMixin):
    '''
    Encapsulates a call to docker-compose in order to deploy a new cluster given a compose file.
    '''

    def __init__(self, compose_path):
        self.compose_path = compose_path

    def deploy(self, compose_definition):
        '''
        Calls docker-compose with the contents of a compose file as input.
        '''

        # save definition in file
        fs_util.create_dir_dont_complain(self.compose_path)
        definition_file = os.path.join(self.compose_path, 'docker-cluster.yml')
        with open(definition_file, 'w') as df:
            df.write(compose_definition)

        # call docker-compose command, should pick up the created file
        # note: apparently, using docker-compose.yml and removing '-f' fails to
        # to acknowledge the --force-recreate option
        #
        # TODO think about privileged containers
        cmd = 'docker-compose --no-ansi -f docker-cluster.yml up -d --force-recreate'
        run = runit.execute(cmd, cwd=self.compose_path)

        # always show the output of the docker-compose call
        print(run[1])

        if run[2]:
            # return code is different than 0, something went wrong
            raise ComposeFailure('docker-compose command failed, check output')
