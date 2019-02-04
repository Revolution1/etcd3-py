import re

SPECS = []

from .v3_0_x import spec_v3_0_x

SPECS.append(('3.0.x', spec_v3_0_x))

from .v3_1_x import spec_v3_1_x

SPECS.append(('3.1.x', spec_v3_1_x))

from .v3_2_x import spec_v3_2_x

SPECS.append(('3.2.x', spec_v3_2_x))

from .v3_3_x import spec_v3_3_x

SPECS.append(('3.3.x', spec_v3_3_x))

def get_spec(server_version=''):
    p = server_version.replace('.', r'\.').replace('x', r'\d+')
    r = re.compile(p)
    for v, spec in SPECS:
        if r.match(v):
            return spec
    if SPECS:
        return SPECS[-1][-1] # return the newest by default
