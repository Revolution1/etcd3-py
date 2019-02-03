import re

PROTOS = []

from .v3_0_x import spec_v3_0_x

PROTOS.append(('3.0.x', spec_v3_0_x))

from .v3_1_x import spec_v3_1_x

PROTOS.append(('3.1.x', spec_v3_1_x))

from .v3_2_x import spec_v3_2_x

PROTOS.append(('3.2.x', spec_v3_2_x))

from .v3_3_x import spec_v3_3_x

PROTOS.append(('3.3.x', spec_v3_3_x))

def get_proto(server_version):
    p = server_version.replace('.', r'\.').replace('x', r'\d+')
    r = re.compile(p)
    for v, spec in PROTOS:
        if r.match(v):
            return spec
    if PROTOS:
        return PROTOS[-1][-1] # return the newest by default
