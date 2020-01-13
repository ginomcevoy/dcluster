import os
import unittest

from dcluster import config


class ConfigTest(unittest.TestCase):
    '''
    Unit tests for dcluster.config
    '''

    def setUp(self):
        self.maxDiff = None

    def test_cluster_config_does_not_get_corrupted(self):
        '''
        config.for_cluster() of an extended cluster config should not affect the config of the
        base cluster config.
        '''
        # when using simple config
        simple_config = config.for_cluster('simple')
        simple_value = simple_config['template']

        # given that an extended config is requested
        _ = config.for_cluster('slurm')

        # then it should not affect the base config
        simple_config_again = config.for_cluster('simple')
        simple_value_again = simple_config_again['template']
        self.assertEqual(simple_value, simple_value_again)

    def test_config_composer_workpath(self):
        # given
        cluster_name = 'mycluster'
        workpath = config.paths('work')

        # when
        composer_workpath = config.composer_workpath(cluster_name)

        # then
        expected = os.path.join(workpath, 'clusters/mycluster')
        self.assertEqual(composer_workpath, expected)
