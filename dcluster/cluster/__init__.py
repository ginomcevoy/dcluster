from dcluster import config

from .deploy import DockerComposeDeployer
from .render import SimpleRenderer


def get_renderer(creation_request):
    '''
    '''
    # only simple for now
    templates_dir = config.paths('templates')
    return SimpleRenderer(templates_dir)


__all__ = ['DockerComposeDeployer']
