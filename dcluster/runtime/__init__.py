from .deploy import DockerComposeDeployer
from .render import JinjaRenderer

from dcluster import config


def get_renderer(creation_request):
    '''
    '''
    # only one type for now
    templates_dir = config.paths('templates')
    return JinjaRenderer(templates_dir)


__all__ = ['DockerComposeDeployer']
