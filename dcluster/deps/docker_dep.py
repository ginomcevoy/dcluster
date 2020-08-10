import distutils.spawn
import logging
import os
import platform
import stat

from runitmockit import runit

from dcluster.util import logger, fs

from . import download
from . import pip_user


DOCKER_COMPOSE_VERSION = '1.25.0'


def ensure_docker_package():
    '''
    Tries to import docker module. If the module is not found, it will try to install docker via
    pip. Exits normally if successful, raises ImportError if the import fails.
    '''
    log = logger.logger_for_me(ensure_docker_package)

    if not pip_user.is_package_installed('docker'):
        # try to install it via pip
        pip_user.install_with_pip('docker')

    # try to import docker, if this fails then give up
    import docker
    log.info('Python API for docker found: {}'.format(docker.__version__))


def ensure_docker_compose():
    '''
    Looks for docker_compose in PATH. If the executable is not found, it will try to download
    it from the docker-compose repository. Exits normally if successful, raises ValueError if
    the executable cannot be downloaded.
    '''
    log = logger.logger_for_me(ensure_docker_package)

    # check for docker-compose in PATH
    docker_compose_path = distutils.spawn.find_executable('docker-compose')

    if not docker_compose_path:
        # prepare to download it at user HOME
        server_url = docker_compose_url()
        output_dir = os.path.expanduser('~/.dcluster/bin')
        fs.create_dir_dont_complain(output_dir)  # ensure download dir
        docker_compose_path = os.path.join(output_dir, 'docker-compose')

        # download if this fails then give up
        download.download_to_file_strict(server_url, docker_compose_path)

        # make it executable
        st = os.stat(docker_compose_path)
        os.chmod(docker_compose_path, st.st_mode | stat.S_IEXEC)

    # check for docker-compose version
    cmd = 'docker-compose -v'
    stdout, stderr, rc = runit.execute(cmd)

    if 'docker-compose' not in stdout or rc != 0:
        err_msg = 'Not able to use docker-compose (rc={}):\n{}\n{}'
        raise ValueError(err_msg.format(rc, stdout, stderr))

    log.info('Found docker-compose at: {}'.format(docker_compose_path))


def docker_compose_url():
    base_url = 'https://github.com/docker/compose/releases/download/{}/docker-compose-{}-{}'
    return base_url.format(DOCKER_COMPOSE_VERSION, platform.system(), platform.machine())


if __name__ == '__main__':
    # test docker presence
    log_level = getattr(logging, 'DEBUG')
    logging.basicConfig(format='%(asctime)s - %(levelname)6s | %(message)s',
                        level=log_level, datefmt='%d-%b-%y %H:%M:%S')
    ensure_docker_package()
    ensure_docker_compose()
