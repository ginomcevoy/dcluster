import os
import yaml

from dcluster import tests


class ResourcesForTest(object):

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

    @property
    def expected_docker_compose_simple(self):
        expected_filename = os.path.join(self.resources_dir, 'docker-compose-simple.yml')
        expected_contents = None
        with open(expected_filename, 'r') as ef:
            expected_contents = ef.read()
        return expected_contents

    @property
    def expected_docker_compose_slurm(self):
        expected_filename = os.path.join(self.resources_dir, 'docker-compose-slurm.yml')
        expected_contents = None
        with open(expected_filename, 'r') as ef:
            expected_contents = ef.read()
        return expected_contents


if __name__ == '__main__':
    tr = ResourcesForTest()
    print(tr.resources_dir)
    print(tr.expected_cluster_inventory)
