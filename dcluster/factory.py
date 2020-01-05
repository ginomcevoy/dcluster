from dcluster.request import simple as request_simple
from dcluster.cluster import simple as simple_cluster

__factories = None


def initialize_factories():
    return {
        'simple': simple_factories()
    }


def simple_factories():
    request_factory = request_simple.SimpleRequestFactory()
    planner = simple_cluster.SimplePlanner()
    return {
        'request': request_factory,
        'planner': planner
    }


def factories_by_flavor(flavor):
    global __factories
    if __factories is None:
        __factories = initialize_factories()
    return __factories[flavor]


def create_request(args):
    flavor = args.flavor
    request_factory = factories_by_flavor(flavor)['request']
    return request_factory.create(args)


def create_plan(request):
    flavor = request.flavor
    planner = factories_by_flavor(flavor)['planner']
    return planner.plan(request)
