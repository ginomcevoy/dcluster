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
        return self.expected_text('docker-compose-simple.yml')

    @property
    def expected_docker_compose_slurm(self):
        return self.expected_text('docker-compose-slurm.yml')

    @property
    def expected_render_extended_simplified(self):
        return self.expected_text('docker-compose-extended-simplified.yml')

    def expected_text(self, filename, resources_dir=None):
        if resources_dir is None:
            # use default value
            resources_dir = self.resources_dir

        expected_filename = os.path.join(resources_dir, filename)
        expected_contents = None
        with open(expected_filename, 'r') as ef:
            expected_contents = ef.read()
        return expected_contents


if __name__ == '__main__':
    tr = ResourcesForTest()
    print(tr.resources_dir)
    print(tr.expected_cluster_inventory)
