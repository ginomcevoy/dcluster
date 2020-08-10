import urllib
import shutil
import ssl
import sys

from dcluster.util import logger


def download_to_file_strict(server_url, output_filename):
    '''
    Downloads the file at baseURL and saves the file
    to output_filename. Overwrites the file.

    Returns None if downloaded, raises error if problem found
    '''
    error = download_to_file(server_url, output_filename)
    if error:
        raise ValueError('Could not download {}: {}'.format(server_url, error))


def download_to_file(server_url, output_filename):
    '''
    Downloads the file at baseURL and saves the file
    to output_filename. Overwrites the file.

    Returns None if downloaded, error string if problem with download
    '''
    log = logger.logger_for_me(download_to_file)

    # ignore bad certificates using monkey patch
    ssl._create_default_https_context = ssl._create_unverified_context

    # code is version dependent
    python_version = sys.version_info[0]
    if python_version < 3:
        return download_to_file_py2(server_url, output_filename, log)
    else:
        return download_to_file_py3(server_url, output_filename, log)


def download_to_file_py2(server_url, output_filename, log):
    '''
    Use with python 2.7+
    '''
    opener = urllib.URLopener()

    try:
        log.info('Downloading: ' + server_url)
        opener.retrieve(server_url, output_filename)
        error = ''

        log.debug('Saved at ' + output_filename)

    except IOError as e:
        log.warn('Could not download {}'.format(server_url))
        log.warn(str(e))
        error = e

    return error


def download_to_file_py3(server_url, output_filename, log):
    '''
    Use with python 3.3+
    '''
    log.info('Downloading: ' + server_url)
    with urllib.request.urlopen(server_url) as response:
        with open(output_filename, 'wb') as output_file:
            shutil.copyfileobj(response, output_file)
            log.debug('Saved at ' + output_filename)
