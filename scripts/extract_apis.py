"""
Tool to generate python api code from swagger spec
"""

import inflection
import jinja2

swagger_types = {
    'string': 'str',
    'integer': 'int',
    'int64': 'int',
    'int32': 'int',
    'uint64': 'int',
    'boolean': 'bool',
    'byte': 'str',
    'object': 'dict'
}


def swagger_type(prop):
    if prop._is_enum:
        return prop._path[-1]
    if prop.type == 'array':
        return 'list of %s' % swagger_types[prop.items.type]
    return swagger_types[prop._get('format', None) or prop.type]


env = jinja2.Environment(autoescape=False)
env.filters['underscore'] = inflection.underscore
env.filters['camelcase'] = inflection.camelize
env.filters['swagger_type'] = swagger_type
env.filters['swagger_description'] = lambda prop: prop.title or prop.description
env.filters['append_spaces'] = lambda s, n: s and ('\n' + ' ' * n).join(s.splitlines())

BASE_FILE = '''\
class BaseAPI(object):
    def call_rpc(self, method, data=None, stream=False, **kwargs):
        raise NotImplementedError
'''

INIT_FILE_TEMPLATE = '''\
from .base import BaseAPI
{% for tag in tags %}\
from .{{ tag | lower }} import {{ tag | camelcase }}API
{% endfor%}

__all__ = [{% for tag in tags %}
    '{{ tag | camelcase }}API',{% endfor %}
    'BaseAPI'
]
'''

API_FILE_TEMPLATE = '''\
from .base import BaseAPI
{% for path in paths %}\
{% set params = path.post.parameters[0].schema %}\
{% if 'properties' in params %}\
{% for prop in params.properties %}\
{% if prop._get('default', None) and prop._is_enum %}from ..models import {{ prop._path[-1] }}{% endif %}
{% endfor %}\
{% endif %}\
{% endfor %}

class {{ tag | camelcase }}API(BaseAPI):
{% for path in paths %}{% set params = path.post.parameters[0].schema %}
    def {{ path.post.operationId | underscore}}(self,
        {% if 'properties' in params %}\
        {% for prop in params.properties %}\
        {% if not prop._get('default', None) %}{{ prop._name }}, {% endif %}
        {% endfor %}\
        {% for prop in params.properties %}\
        {% if prop._get('default', None) %}\
        {% if prop._is_enum %}{{ prop._name }}={{ prop._path[-1] }}.{{ prop.default }}, {% endif %}
        {% endif %}\
        {% endfor %}\
        {% endif %}\
    ):
        """
        {{ path.post.summary | append_spaces(8)}}
        {% if 'properties' in params %}{% for prop in params.properties %}
        :type {{ prop._name }}: {{ prop | swagger_type }}
        :param {{ prop._name }}: {{ prop | swagger_description | append_spaces(12) }}{% endfor %}{% endif %}
        """
        method = '{{ path._name }}'
        data = {}
        return self.call_rpc(method, data=data)
        
{% endfor %}
'''

if __name__ == '__main__':
    import os
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

    import jinja2
    from etcd3.swagger_helper import SwaggerSpec
    from yapf.yapflib.yapf_api import FormatCode
    from isort import SortImports

    GENERATED_APIS_DIR = os.path.join(os.path.dirname(__file__), '../etcd3/apis_generated')

    rpc_swagger_json = os.path.join(os.path.dirname(__file__), '../etcd3/rpc.swagger.json')
    swaggerSpec = SwaggerSpec(rpc_swagger_json)

    api_tpl = env.from_string(API_FILE_TEMPLATE)
    init_tpl = env.from_string(INIT_FILE_TEMPLATE)

    # ensure dir
    if not os.path.exists(GENERATED_APIS_DIR):
        os.mkdir(GENERATED_APIS_DIR)

    with open(os.path.join(GENERATED_APIS_DIR, 'base.py'), 'w') as f:
        f.write(BASE_FILE)

    tags = {}
    for path in swaggerSpec.paths:
        tags.setdefault(path.post.tags[0], []).append(path)

    for tag, paths in tags.items():
        with open(os.path.join(GENERATED_APIS_DIR, '%s.py' % tag.lower()), 'w') as f:
            s = api_tpl.render(tag=tag, paths=paths)
            f.write(SortImports(file_contents=FormatCode(s, style_config='pep8')[0], force_single_line=True).output)

    with open(os.path.join(GENERATED_APIS_DIR, '__init__.py'), 'w') as f:
        s = init_tpl.render(tags=tags)
        f.write(SortImports(file_contents=FormatCode(s, style_config='pep8')[0], force_single_line=True).output)
