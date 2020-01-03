import jinja2
import logging
import os

from runitmockit import runit

from dcluster import config
from dcluster import util

from dcluster.docker_facade import DockerNaming

from dcluster.cluster import ClusterBuilder, ComposeFailure


class ClusterBuilderSimple(ClusterBuilder):
    '''
    Builds clusters using the 'simple' configuration, see configuration files.
    '''

    def __init__(self):
        super(ClusterBuilderSimple, self).__init__()
        self.cluster_config = config.cluster('simple')

    def build(self, simple_request, basepath):
        '''
        Creates a simple cluster. It has the specified compute count and a head node.
        The network is created first, then the containers.

        This does not return an instance of DockerCluster yet...
        '''
        self.log.debug('Building cluster of type simple with request %s' % (simple_request,))

        # base behavior
        cluster_network = self.create_network(simple_request)
        cluster_specs = self.build_specs(simple_request, cluster_network)

        # create the containers based on the specification
        compose_path = os.path.join(basepath, simple_request.name)
        composer = ClusterComposerSimple(compose_path, self.templates_dir)
        definition = composer.build_definition(cluster_specs, 'cluster-simple.yml.j2')
        composer.compose(definition)

        log_msg = 'Docker cluster %s -  %s created!'
        self.log.info(log_msg % (cluster_network.network_name, cluster_network))

    def build_specs(self, simple_request, cluster_network):
        '''
        Creates a dictionary of node specs that is needed to later use docker-compose.
        Since we are only building a single type of cluster, we can leave this here.

        A cluster always has a single head, and zero or more compute nodes, depending
        on compute_count.

        Example output: for compute_count = 3, add a head node and 3 compute nodes:

        cluster_specs = {
            'nodes' : {
                '172.30.0.253': {
                    'hostname': 'head',
                    'container': 'mycluster-head',
                    'image': 'centos7:ssh',
                    'ip_address': '172.30.0.253',
                    'type': 'head'
                },
                '172.30.0.1': {
                    'hostname': 'node001',
                    'container': 'mycluster-node001',
                    'image': 'centos7:ssh',
                    'ip_address': '172.30.0.1',
                    'type': 'compute'
                },
                '172.30.0.2': {
                    'hostname': 'node002',
                    'container': 'mycluster-node002',
                    'image': 'centos7:ssh',
                    'ip_address': '172.30.0.2',
                    'type': 'compute'
                },
                '172.30.0.3': {
                    'hostname': 'node003',
                    'container': 'mycluster-node003',
                    'image': 'centos7:ssh',
                    'ip_address': '172.30.0.3',
                    'type': 'compute'
                }
            }
            'network': {
                'name': 'dcluster-mycluster',
                'ip_address': '172.30.0.0/24'
                'gateway_hostname': 'gateway'
                'gateway_ip': '172.30.0.254'
            }
        }
        '''

        cluster_name = simple_request.name
        head_ip = cluster_network.head_ip()
        head_hostname = self.cluster_config['head']['hostname']
        head_image = self.cluster_config['head']['image']

        # always have a head and a network
        head_entry = self.create_node_entry(cluster_name, head_hostname, head_ip,
                                            head_image, 'head')
        network_entry = cluster_network.as_dict()

        cluster_specs = {
            'nodes': {
                head_ip: head_entry
            },
            'network': network_entry
        }

        # add compute nodes, should raise NetworkSubnetTooSmall if there are not enough IPs
        compute_ips = cluster_network.compute_ips(simple_request.compute_count)
        compute_image = self.cluster_config['compute']['image']

        for index, compute_ip in enumerate(compute_ips):

            compute_hostname = self.create_compute_hostname(index)
            node_entry = self.create_node_entry(cluster_name, compute_hostname,
                                                compute_ip, compute_image, 'compute')
            cluster_specs['nodes'][compute_ip] = node_entry

        return cluster_specs

    def build_slurm(self, slurm_request, basepath):
        '''
        Create a cluster meant to support Slurm.
        '''
        self.log.debug('Building cluster of type slurm with request %s' % (slurm_request,))
        raise NotImplementedError('slurm')

    def create_compute_hostname(self, index):
        '''
        Returns the hostname of a compute node given its index.

        Ex.
        0 -> node001
        1 -> node002
        '''
        name_prefix = self.cluster_config['compute']['hostname']['prefix']
        suffix_len = self.cluster_config['compute']['hostname']['suffix_len']

        suffix_str = '{0:0%sd}' % str(suffix_len)
        suffix = suffix_str.format(index + 1)
        return name_prefix + suffix

    def create_node_entry(self, cluster_name, hostname, ip_address, image, node_type):
        '''
        Create an entry for node specs. The container name is inferred from the hostname.
        '''

        container_name = DockerNaming.create_container_name(cluster_name, hostname)

        return {
            'hostname': hostname,
            'container': container_name,
            'image': image,
            'ip_address': ip_address,
            'type': node_type
        }


class ClusterComposerSimple(object):

    def __init__(self, compose_path, templates_dir):
        self.compose_path = compose_path
        self.templates_dir = templates_dir

        self.log = logging.getLogger()

    def build_definition(self, cluster_specs, template_filename):

        # build the replacement dictionary
        replacements = dict(**cluster_specs)
        self.log.debug(replacements)

        # Load Jinja2 template
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(self.templates_dir),
                                 trim_blocks=True, lstrip_blocks=True)

        template = env.get_template(template_filename)
        compose_definition = template.render(**replacements)
        self.log.debug(compose_definition)
        return compose_definition

    def compose(self, compose_definition):

        # save definition in file
        util.create_dir_dont_complain(self.compose_path)
        definition_file = os.path.join(self.compose_path, 'docker-cluster.yml')
        with open(definition_file, 'w') as df:
            df.write(compose_definition)

        # call docker-compose command, should pick up the created file
        # note: apparently, using docker-compose.yml and removing '-f' fails to
        # to acknowledge the --force-recreate option
        cmd = 'docker-compose --no-ansi -f docker-cluster.yml up -d --force-recreate'
        run = runit.execute(cmd, cwd=self.compose_path)
        print(run[1])

        if run[2]:
            raise ComposeFailure('docker-compose command failed, check output')
