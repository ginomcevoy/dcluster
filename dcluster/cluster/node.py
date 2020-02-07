from operator import attrgetter

from dcluster.docker_facade import DockerContainers, DockerNetworking
from dcluster.plan.simple import SimplePlannedNode
from dcluster import logger


def planned_from_docker(docker_container, docker_network):
    return SimplePlannedNode(
        hostname=DockerContainers.hostname(docker_container),
        container=docker_container.name,
        image=docker_container.image.tags[0],
        ip_address=DockerContainers.ip_address(docker_container, docker_network),
        # check the labels of the docker object, requires Docker 17.06.0+ / compose 3.3+
        role=DockerContainers.role(docker_container)
    )


class DeployedNode(logger.LoggerMixin):
    '''
    Encapsulates docker-specific implementation of a container and its attributes.
    Assumes it is part of a docker cluster.

    TODO extend SimplePlannedNode like this
    https://stackoverflow.com/questions/42385916/inheriting-from-a-namedtuple-base-class-python

    but ONLY if it is worth it...
    '''

    def __init__(self, docker_container, docker_network):
        self.docker_container = docker_container
        self.docker_network = docker_network
        self.planned = planned_from_docker(docker_container, docker_network)

    @property
    def hostname(self):
        return self.planned.hostname

    @property
    def container(self):
        return self.docker_container

    @property
    def image(self):
        return self.docker_container.image

    @property
    def ip_address(self):
        return self.planned.ip_address

    @property
    def role(self):
        return self.planned.role

    def inject_public_ssh_key(self, ssh_target_path, public_key):
        '''
        Injects the SSH public_key (provided as string), and injects it to the node container.
        This is done by executing the echo command on the .ssh/authorized_keys.
        '''
        run_cmd_template = '/bin/bash -c "mkdir -p %s && echo %s >> %s/authorized_keys"'
        run_cmd = run_cmd_template % (ssh_target_path, public_key, ssh_target_path)

        log_msg = 'Run in docker container %s: %s'
        self.logger.debug(log_msg % (self.docker_container.name, run_cmd))

        self.docker_container.exec_run(run_cmd)

    @classmethod
    def find_for_cluster(cls, cluster_name, docker_network=None):
        if not docker_network:
            docker_network = DockerNetworking.find_network(cluster_name)

        cluster_containers = DockerNetworking.containers_in_network(docker_network)
        deployed_nodes = [
            DeployedNode(docker_container, docker_network)
            for docker_container
            in cluster_containers
        ]
        return sorted(deployed_nodes, key=attrgetter('ip_address'))
