from collections import namedtuple


# node details used when recovering node details from docker
BasicPlannedNode = namedtuple('BasicPlannedNode', 'hostname, container, image, ip_address, role')

# node details for the 'default' plan when creating a cluster
DefaultPlannedNode = namedtuple('DefaultPlannedNode', 'hostname, container, image, ip_address, \
                                role, hostname_alias, volumes, static_text, systemctl')
