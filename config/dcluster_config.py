
__dcluster_config = None


def get(key):
    global __dcluster_config
    if __dcluster_config is None:
        dcluster_config = {
            'templates_dir': '/home/giacomo/dev/atos/dcluster/templates',
        }
    return dcluster_config[key]
