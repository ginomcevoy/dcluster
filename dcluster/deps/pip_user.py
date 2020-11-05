import distutils.spawn
import logging
import pkg_resources
import sys

from dcluster.util import logger, runit


def detect_pip_version():
    '''
    Finds the appropriate pip command, one of: pip, pip2, pip3.
    '''

    # if using Python3, try pip3
    # if using Python2, try pip2
    pip_candidate = 'pip{}'.format(sys.version_info[0])
    found = distutils.spawn.find_executable(pip_candidate)

    if not found:
        raise ValueError('pip not found in PATH, tried: {}'.format(pip_candidate))

    return pip_candidate


def is_package_installed(package_name):
    '''
    Tests if a package has been installed using setuptools (also works for pip).
    Requires setuptools.
    '''
    # Based on https://stackoverflow.com/a/51931735
    try:
        pkg_resources.get_distribution(package_name)
    except pkg_resources.DistributionNotFound:
        return False
    else:
        return True


def install_with_pip(package_name):
    '''
    Calls pip install --user <package_name>.
    '''
    log = logger.logger_for_me(install_with_pip)
    my_pip = detect_pip_version()
    cmd = '{} install --user {}'.format(my_pip, package_name)
    log.debug('Calling: >>{}<<'.format(cmd))
    runit.execute(cmd, logger=log, log_level=logging.INFO)


if __name__ == '__main__':
    # test pip install
    log_level = getattr(logging, 'DEBUG')
    logging.basicConfig(format='%(asctime)s - %(levelname)6s | %(message)s',
                        level=log_level, datefmt='%d-%b-%y %H:%M:%S')

    print(is_package_installed('docker'))
    install_with_pip('pip')
