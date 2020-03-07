from collections import namedtuple


# node details for the 'basic' plan
BasicPlannedNode = namedtuple('BasicPlannedNode', 'hostname, container, image, ip_address, role')

# node details for the 'extended' plan
ExtendedPlannedNode = namedtuple('ExtendedPlannedNode',
                                 'hostname, container, image, ip_address, role, volumes, \
                                  static_text')
