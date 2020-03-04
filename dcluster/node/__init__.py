from collections import namedtuple


SimplePlannedNode = namedtuple('SimplePlannedNode', 'hostname, container, image, ip_address, role')

ExtendedPlannedNode = namedtuple('ExtendedPlannedNode',
                                 'hostname, container, image, ip_address, role, volumes, \
                                  static_text')
