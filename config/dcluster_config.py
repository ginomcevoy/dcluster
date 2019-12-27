
__dcluster_config = None


def get(key):
    global __dcluster_config
    if __dcluster_config is None:
        dcluster_config = {
            'ansible_static_path': '/home/giacomo/dev/atos/clustertest/ansible_static'
        }
    return dcluster_config[key]
