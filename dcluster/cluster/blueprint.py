from dcluster.util import logger


class ClusterBlueprint(logger.LoggerMixin):
    '''
    Represents a cluster ready to be deployed.
    Also used to represent a deployed cluster (see instance.DeployedCluster).
    '''

    def __init__(self, cluster_network, cluster_specs):
        self.cluster_network = cluster_network
        self.cluster_specs = cluster_specs

        # small initialization to have a list of nodes handy
        ordered_node_ips = sorted(cluster_specs['nodes'].keys())
        self.ordered_nodes = [
            cluster_specs['nodes'][ordered_ip]
            for ordered_ip
            in ordered_node_ips
        ]

    def deploy(self, renderer, deployer):
        template = self.cluster_specs['template']
        cluster_definition = renderer.render_blueprint(self.as_dict(), template)
        deployer.deploy(cluster_definition)
        # deployed_cluster = cluster.from_docker(name)

        log_msg = 'Docker cluster %s -  %s created!'
        self.logger.info(log_msg % (self.name, self.cluster_network))

    @property
    def name(self):
        return self.cluster_specs['name']

    def nodes_by_role(self, role):
        '''
        Returns a list of the nodes that are of some role
        '''
        return [
            n
            for n in self.ordered_nodes
            if n.role == role
        ]

    @property
    def head_node(self):
        return self.nodes_by_role('head')[0]

    @property
    def gateway_node(self):
        return self.nodes_by_role('gateway')[0]

    @property
    def compute_nodes(self):
        return self.nodes_by_role('compute')

    def format(self, formatter):
        '''
        Format the cluster to some representation, e.g. as text.
        '''
        return formatter.format(self.as_dict())

    def as_dict(self):
        '''
        Dictionary version of ClusterBlueprint
        '''
        return self.cluster_specs