import unittest

from dcluster.config import main_config


class DclusterTest(unittest.TestCase):

    '''
    All unit tests for dcluster should inherit from this class, this ensures that the "dev" preferences
    are read even if running on a production environment.
    '''

    @classmethod
    def setUpClass(cls):
        orig_config = main_config.get_config()
        dev_config = main_config.create_dev_config()
        orig_config['prefs'] = dev_config['prefs']
