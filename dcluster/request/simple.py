from collections import namedtuple


# represents a 'simple' cluster with the specified count of compute nodes.
# it should also have a head node.
ClusterRequestSimple = namedtuple('ClusterRequestSimple', ['name', 'compute_count', 'flavor'])


class SimpleRequestFactory(object):

    def create(self, args):
        count = int(args.compute_count)
        return ClusterRequestSimple(args.cluster_name, count, args.flavor)
