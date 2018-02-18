ENUM_FILE_TPL = '''\
# Models generated from rpc.swagger.json, do not edit
import enum

{% for e in enums %}
class {{e._path | last}}(enum.Enum):
    """
    ref: {{ e._ref }}
    default: {{ e.default }}
    """
    {% for prop in e.enum %}{{ prop.name }} = '{{ prop.value }}'
    {% endfor %}
{% endfor %}
__all__ = [{% for e in enums %}
    '{{e._path | last}}',{% endfor %}
]

'''

if __name__ == '__main__':
    import os
    import jinja2
    from swagger_helper import SwaggerSpec

    rpc_swagger_json = os.path.join(os.path.dirname(__file__), 'rpc.swagger.json')
    swaggerSpec = SwaggerSpec(rpc_swagger_json)

    enums = [i for i in swaggerSpec.definitions if i._is_enum]
    enum_tpl = jinja2.Template(ENUM_FILE_TPL)
    with open(os.path.join(os.path.dirname(__file__), 'models.py'), 'w') as f:
        s = enum_tpl.render(enums=enums)
        f.write(s)
        print(s)
