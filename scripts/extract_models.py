ENUM_FILE_TPL = '''\
# Models generated from rpc.swagger.json, do not edit
# flake8: noqa
import enum

class EtcdModel(object):
    pass

{% for e in enums %}
class {{e._path | last}}(EtcdModel, enum.Enum):
    """
    ref: {{ e._ref }}

    default: {{ e.default }}
    """
    {% for prop in e.enum %}{{ prop.name }} = '{{ prop.value }}'
    {% endfor %}
{% endfor %}
name_to_model = {
{% for e in enums %}
    '{{e._path | last}}': {{e._path | last}},{% endfor %}
}
__all__ = [{% for e in enums %}
    '{{e._path | last}}',
    {% endfor %}
    'name_to_model', 'EtcdModel',
]

'''

DEFAULT_MODEL_VERSION = '3.3.0'

if __name__ == '__main__':
    import os
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

    import jinja2
    from yapf.yapflib.yapf_api import FormatCode
    from isort import SortImports

    from etcd3.swagger_helper import SwaggerSpec
    from etcd3.swaggerdefs import get_spec

    swaggerSpec = SwaggerSpec(get_spec(DEFAULT_MODEL_VERSION))

    enums = [i for i in swaggerSpec.definitions if i._is_enum]
    enum_tpl = jinja2.Template(ENUM_FILE_TPL)
    with open(os.path.join(os.path.dirname(__file__), '../etcd3/models.py'), 'w') as f:
        s = enum_tpl.render(enums=enums)
        s = SortImports(file_contents=FormatCode(s, style_config='pep8')[0], force_single_line=True).output
        f.write(s)
        print(s)
