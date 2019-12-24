import os
import yaml

from dcluster import tests


class TestResources(object):

    def __init__(self):
        # full path of the test module
        test_file_location = tests.__file__

        test_dir = os.path.dirname(test_file_location)
        self.resources_directory = os.path.join(test_dir, tests.RESOURCES_DIR)

    @property
    def resources_dir(self):
        return self.resources_directory

    @property
    def expected_cluster_inventory(self):
        expected_filename = os.path.join(self.resources_dir, 'expected-cluster.yml')
        self.expected_dict = None
        with open(expected_filename, 'r') as ef:
            expected_dict = yaml.load(ef)
        return expected_dict


if __name__ == '__main__':
    tr = TestResources()
    print(tr.resources_dir)
    print(tr.expected_cluster_inventory)
