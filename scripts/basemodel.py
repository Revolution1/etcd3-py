# no use for now
import enum

import six


class BaseModel(object):
    pass


class ObjectModel(BaseModel):
    def __init__(self, data, node):
        if not isinstance(data, dict):
            raise TypeError("A dict expected, got a '%s' instead" % type(data))
        self._node = node
        self._data = data
        self._name = node._path[-1]
        for k in node.properties._keys():
            if k not in data:
                continue
            v = data[k]
            m = node.properties._get(k)
            if m._is_schema:
                m = m.getModel()
                v = m(v)
            setattr(self, k, v)

    def __iter__(self):
        return iter(self._data)

    def __contains__(self, item):
        return item in self._data

    def __repr__(self):
        return '%s(%s)' % (
            self._name,
            ', '.join(['%s=%s' % (k, repr(v)) for k, v in six.iteritems(self.__dict__) if k in self._data])
        )


class ArrayModel(BaseModel, list):
    def __init__(self, data, node):
        if not isinstance(data, (list, tuple)):
            raise TypeError("A list or tuple expected, got a '%s' instead" % type(data))
        self._data = data
        self._node = node
        m = node.items.getModel()
        for i in data:
            self.append(m(i))


class ImmutableModel(BaseModel):
    def __init__(self, data):
        self._data = data

    def __get__(self, instance, owner):
        if isinstance(self._data, enum.Enum):
            return self._data.value
        return self._data
