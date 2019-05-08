import os
import sys

root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root)

import jinja2
from yapf.yapflib.yapf_api import FormatCode
from isort import SortImports

with open(os.path.join(root, 'etcd3/swaggerdefs/v3_3_x/__init__.py')) as f:
    g = {}
    exec(f.read(), g)
    spec = g.get('spec_v3_3_x')

with open(os.path.join(root, 'scripts/model-template.jinja2')) as f:
    model_tpl = jinja2.Template(f.read(), trim_blocks=True, lstrip_blocks=True)

with open(os.path.join(os.path.dirname(__file__), '../etcd3/models.py'), 'w') as f:
    s = model_tpl.render(spec=spec)
    print(s)
    s = SortImports(file_contents=FormatCode(s, style_config='pep8')[0], force_single_line=True).output
    f.write(s)
    print(s)
