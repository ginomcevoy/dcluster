from collections import namedtuple


BasicPlannedNode = namedtuple('BasicPlannedNode', 'hostname, container, image, ip_address, role')

ExtendedPlannedNode = namedtuple('ExtendedPlannedNode',
                                 'hostname, container, image, ip_address, role, volumes, \
                                  static_text')
