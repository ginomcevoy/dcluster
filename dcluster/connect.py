'''
Store the singleton for a client connection to Docker.
Requires the user to be in the 'docker' group.
'''

import docker


__docker_client = None


def client():
    global __docker_client
    if __docker_client is None:
        __docker_client = docker.from_env()        
    return __docker_client
