from operator import attrgetter


class SimpleFormatter(object):
    '''
    Formats a simple cluster as text.
    '''

    def format(self, cluster_dict):
        lines = [''] * 6
        lines[0] = 'Cluster: %s' % cluster_dict['name']
        lines[1] = '-' * 24
        lines[2] = 'Network: %s' % cluster_dict['network']['subnet']
        lines[3] = ''

        node_format = '  {:15}{:16}{:25}'

        # header of nodes
        lines[4] = node_format.format('hostname', 'ip_address', 'container')
        lines[5] = '  ' + '-' * 48

        sorted_node_info = sorted(cluster_dict['nodes'].values(), key=attrgetter('hostname'))

        node_lines = [
            # format namedtuple contents
            node_format.format(node.hostname, node.ip_address, node.container.name)
            for node
            in sorted_node_info
        ]

        lines.extend(node_lines)
        lines.append('')
        return '\n'.join(lines)
