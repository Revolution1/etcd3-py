import base64
import copy
import json
import keyword
import os
import re

import enum
import functools32
import six

try:
    import yaml
except:
    yaml = None


def swagger_escape(s):
    return s.replace('~', '~0').replace('/', '~1')


def _format_path(path):
    if isinstance(path, (int, float)) or path.isdigit():
        return '_%s' % path
    if keyword.iskeyword(path):
        return '%s_' % path
    path = path.lstrip('/')
    return re.sub(r'\W', '_', path)


def _get_path(node, key, default=None):
    n = node.get(key, default)
    if key not in node:
        for k, v in six.iteritems(node):
            if _format_path(k) == key:
                n = v
                break
    return n


class SwaggerSpec(object):
    def __init__(self, spec):
        if isinstance(spec, dict):
            spec_content = spec
        elif isinstance(spec, file):
            pos = spec.tell()
            spec_content = spec.read()
            spec.seek(pos)
        elif isinstance(spec, six.string_types):
            if len(spec) < 255 and os.path.isfile(spec):
                with open(spec, 'r') as f:
                    spec_content = f.read()
            else:
                spec_content = spec
        else:
            raise TypeError('spec should be one of path, file obj, spec string')
        if isinstance(spec_content, dict):
            self.spec = spec_content
        else:
            try:
                self.spec = json.loads(spec_content)
            except:
                if not yaml:
                    raise ImportError("No module named yaml")
                try:
                    self.spec = yaml.safe_load(spec_content)
                except:
                    raise ValueError("Fail to load spec")

    @functools32.lru_cache()
    def _ref(self, ref):
        if not ref.startswith('#/'):
            return None, None
        else:
            path = ref[2:].split('/')
            rt = self.spec
            for p in path:
                rt = _get_path(rt, p, {})
            if not rt:
                raise ValueError("No reference '%s' found" % ref)
            return rt, path

    def ref(self, ref_path):
        ref, path = self._ref(ref_path)
        if not isinstance(ref, dict):
            return ref
        return SwaggerNode(self, ref, path, self)

    def get(self, key, *args, **kwargs):
        return self.spec.get(key, *args, **kwargs)

    @functools32.lru_cache()
    def getPath(self, key):
        """
        get a SwaggerPath instance of the path
        :type key:SwaggerNode or str
        :param key: receive a SwaggerNode or a $ref string of schema
        :rtype: SwaggerNode
        """
        if key in self.spec['paths']:
            node = self.paths[key]
        elif isinstance(key, SwaggerNode):
            node = key
        else:
            node = self.ref(key)
        return node

    @functools32.lru_cache()
    def getSchema(self, key):
        """
        get a SwaggerSchema instance of the schema
        :type key:SwaggerNode or str
        :param key: receive a SwaggerNode or a $ref string of schema
        :rtype: SwaggerNode
        """
        if key in self.spec['definitions']:
            node = self.definitions[key]
        elif isinstance(key, SwaggerNode):
            node = key
        else:
            node = self.ref(key)
        return node

    def getEnum(self, key):
        """
        get a Enum instance of the schema
        :type key:SwaggerNode or str
        :param key: receive a SwaggerNode or a $ref string of schema
        :rtype: SwaggerNode
        """
        schema = self.getSchema(key)
        if not schema._is_enum:
            raise TypeError("schema %s is not a enum" % key)
        return schema.enum

    def __getattribute__(self, key):
        if key != 'spec' and key in self.spec:
            if not isinstance(self.spec[key], dict):
                return self.spec[key]
            try:
                return SwaggerNode(self, self.spec[key], [key], self)
            except KeyError:
                raise AttributeError(
                    r"'{name}' object has no attribute {key}".format(name=self.__name__, key=key))
        else:
            return super(SwaggerSpec, self).__getattribute__(key)

    def __dir__(self):
        return [k for k in type(self).__dict__.keys() if not k.startswith('__')] + self.spec.keys()

    def __repr__(self):
        return "<SwaggerSpec '%s'>" % self.spec.get('info', {}).get('title')


# only support some of https://swagger.io/docs/specification/data-models/data-types/
PROP_ENCODERS = {
    None: lambda x: x,
    'string': lambda x: x,
    'integer': lambda x: int(x) if x is not None else x,
    'int64': lambda x: int(x) if x is not None else x,
    'int32': lambda x: int(x) if x is not None else x,
    'uint64': lambda x: abs(int(x)) if x is not None else x,
    'boolean': lambda x: bool(x) if x is not None else x,
    'byte': lambda x: base64.b64encode(x) if x is not None else x
}

PROP_DECODERS = {
    None: lambda x: x,
    'string': lambda x: x,
    'integer': lambda x: int(x) if x is not None else x,
    'int64': lambda x: int(x) if x is not None else x,
    'int32': lambda x: int(x) if x is not None else x,
    'uint64': lambda x: abs(int(x)) if x is not None else x,
    'boolean': lambda x: bool(x) if x is not None else x,
    'byte': lambda x: base64.b64decode(x) if x is not None else x
}

SCHEMA_TYPES = ('string', 'number', 'integer', 'boolean', 'array', 'object')


class SwaggerNode(object):
    def __init__(self, root, node, path, parent=None):
        self._root = root
        self._node = node
        self._path = path
        self._parent = parent
        self._is_path = False
        if len(self._path) > 1 and self._path[-2] == 'paths':
            self._is_path = True
        self._is_enum = False
        self._is_schema = False
        # and node.get('type') in SCHEMA_TYPES:  # is a schema
        if node.get('type') and isinstance(node['type'], six.string_types):
            self._is_schema = True
            self.type = node.get('type', None)
            self.description = node.get('description', None)
            self.title = node.get('title', None)
            self.required = node.get('required', False)
            if self.type == 'object':
                def encode(data):
                    """
                    :param data: dict
                    """
                    if data is None:
                        return
                    if 'properties' not in node:
                        return {}
                    rt = {}
                    for k, v in self.properties._items():
                        value = self.properties._get(k).encode(data.get(k))
                        if value is None:
                            continue
                        rt[k] = value
                    return rt

                def decode(data):
                    """
                    :param data: dict
                    """
                    if 'properties' not in node:
                        return {}
                    rt = {}
                    for k, v in six.iteritems(data):
                        if k not in self.properties:
                            continue
                        rt[k] = self.properties._get(k).decode(v)
                    return rt

                def getModel():
                    def init(this, data):
                        if not isinstance(data, dict):
                            raise TypeError("A dict expected, got a '%s' instead" % type(data))
                        this._node = self
                        this._data = data
                        for k in self.properties._keys():
                            if not k in data:
                                continue
                            v = data[k]
                            m = self.properties._get(k)
                            if m._is_schema:
                                m = m.getModel()
                                v = m(v)
                            setattr(this, k, v)

                    name = self._path[-1]
                    rep = lambda self: '%s(%s)' % (name, ', '.join(
                        ['%s=%s' % (k, repr(v)) for k, v in six.iteritems(self.__dict__) if k in self._data]))

                    return type(str(name), (), {'__init__': init, '__repr__': rep})

            elif self.type == 'array':

                def encode(data):
                    """
                    :param data: iterable
                    """
                    if data is None:
                        return
                    return [self.items.encode(i) for i in data]

                def decode(data):
                    """
                    :param data: iterable
                    """
                    if data is None:
                        return
                    return [self.items.decode(i) for i in data]

                def getModel():
                    def init(data):
                        if not isinstance(data, (list, tuple)):
                            raise TypeError("A list or tuple expected, got a '%s' instead" % type(data))
                        m = self.items.getModel()
                        return [m(i) for i in data]

                    return init
            elif self.type in PROP_DECODERS:
                def encode(data):
                    rt = PROP_ENCODERS[self.type](PROP_ENCODERS[self.format](data))
                    if self.default and rt is None:
                        return copy.copy(self.default)
                    return rt

                def decode(data):
                    return PROP_DECODERS[self.format](PROP_DECODERS[self.type](data))

                def getModel():
                    return lambda x: x.value if isinstance(x, enum.Enum) else x

                self.format = node.get('format', None)
                self.default = node.get('default', None)
                if 'enum' in node:
                    self._is_enum = True
                    self.enum = enum.Enum(self._path[-1], [(six.text_type(i), i) for i in node.get('enum')])
            else:
                raise TypeError('Unsupported Type %s' % self.type)
            self.encode = encode
            self.decode = decode
            self.getModel = getModel

    @property
    def _ref(self):
        return '#/%s' % '/'.join(self._path)

    def _keys(self):
        return self._node.keys()

    def _values(self):
        return self._node.values()

    def _items(self):
        return six.iteritems(self._node)

    @functools32.lru_cache()
    def __getattr__(self, key):
        try:
            n = _get_path(self._node, key)
            if not n:
                n = self._node[key]
            if isinstance(n, dict):
                ref = n.get('$ref')
                if ref:
                    ref, path = self._root._ref(ref)
                    if not ref:
                        return SwaggerNode(self._root, n, path, self)
                    ref = copy.copy(ref)
                    for k, v in six.iteritems(n):
                        if k != '$ref':
                            ref[k] = v
                    return SwaggerNode(self._root, ref, path, self)
                path = self._path[:]
                path.append(_format_path(key))
                return SwaggerNode(self._root, n, path, self)
            if isinstance(n, (list, tuple)):
                rt = []
                for index, item in enumerate(n):
                    if not isinstance(item, dict):
                        rt.append(item)
                        continue
                    path = self._path[:]
                    path.append('%s__%s' % (_format_path(key), index))
                    rt.append(SwaggerNode(self._root, item, path, self))
                return rt
            return n
        except KeyError:
            raise AttributeError(
                r"no attribute {key}".format(key=key))

    def _get(self, k, *args, **kwargs):
        return getattr(self, k, *args, **kwargs)

    __getitem__ = _get

    def __dir__(self):
        return [k for k in type(self).__dict__.keys() if not k.startswith('__')] \
               + [_format_path(k) for k in self._node.keys()]

    def __contains__(self, item):
        return item in self._node

    def __repr__(self):
        if self._is_path:
            return "SwaggerPath(ref='%s')" % self._ref
        if self._is_schema:
            return "SwaggerSchema(ref='%s')" % self._ref
        return "SwaggerNode(ref='%s')" % self._ref


if __name__ == '__main__':
    with open(os.path.join(os.path.dirname(__file__), 'rpc.swagger.json')) as f:
        spec = json.load(f)
    sh = SwaggerSpec(spec)
    dir(sh)
    dir(sh.paths['/v3alpha/auth/authenticate'])
    print(sh.swagger)
    print(sh.info.title)
    print(sh.info.version)
    print(sh.schemes)
    print(sh.consumes)
    print(sh.produces)
    print(sh.paths['/v3alpha/auth/authenticate'])
    print(sh.getPath('/v3alpha/auth/authenticate'))
    print(sh.paths.v3alpha_auth_authenticate.post.parameters)
    print(sh.ref('#/paths/v3alpha_auth_disable/post/summary'))
    print(sh.ref('#/definitions/etcdserverpbAlarmResponse').properties.alarms.type)
    print(sh.getSchema('etcdserverpbTxnResponse'))
    print(sh.getSchema('etcdserverpbMemberUpdateRequest'))
    etcdserverpbDeleteRangeRequest = sh.getSchema('etcdserverpbDeleteRangeRequest')
    data = dict(key='foo', range_end='foz', prev_kv=1)
    encoded = etcdserverpbDeleteRangeRequest.encode(data)
    print(encoded)
    decoded = etcdserverpbDeleteRangeRequest.decode(encoded)
    print(decoded)
    print(sh.definitions._get('etcdserverpbDeleteRangeRequest').encode(dict(key='foo', range_end='foz', prev_kv=1)))

    etcdserverpbAlarmRequest = sh.getSchema('etcdserverpbAlarmRequest')
    data = dict()
    encoded = etcdserverpbAlarmRequest.encode(data)
    print(encoded)
    decoded = etcdserverpbAlarmRequest.decode(encoded)
    print(decoded)

    print(sh.getSchema('etcdserverpbRangeResponse').getModel()({u'count': u'1',
                                                                u'header': {u'raft_term': u'2', u'revision': u'10',
                                                                            u'cluster_id': u'11588568905070377092',
                                                                            u'member_id': u'128088275939295631'},
                                                                u'kvs': [
                                                                    {u'mod_revision': u'10', u'value': u'YmFy',
                                                                     u'create_revision': u'5', u'version': u'6',
                                                                     u'key': u'Zm9v'}]}))
