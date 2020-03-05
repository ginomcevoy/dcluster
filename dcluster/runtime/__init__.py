from .deploy import DockerComposeDeployer
from .render import JinjaRenderer

from dcluster.config import main_config


def get_renderer(creation_request):
    '''
    '''
    # only one type for now
    templates_dir = main_config.paths('templates')
    return JinjaRenderer(templates_dir)


__all__ = ['DockerComposeDeployer']
