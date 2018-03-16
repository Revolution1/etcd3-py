import functools
import itertools
from collections import namedtuple, OrderedDict, Hashable
from threading import Lock

try:
    from inspect import getfullargspec as getargspec
except ImportError:
    from inspect import getargspec
import six
from six import wraps

_CacheInfo = namedtuple("CacheInfo", "hits misses maxsize currsize")

if six.PY2:
    class OrderedDictEx(OrderedDict):
        """
        On python2, this is a OrderedDict with extended method 'move_to_end'
        that is compatible with collections.OrderedDict in python3

        On python3 it is collections.OrderedDict
        """

        def move_to_end(self, key):
            """
            faster than d[k] = d.pop(k)
            """
            link_prev, link_next, _ = self._OrderedDict__map[key]
            link_prev[1] = link_next  # update link_prev[NEXT]
            link_next[0] = link_prev  # update link_next[PREV]
            root = self._OrderedDict__root
            last = root[0]
            last[1] = root[0] = self._OrderedDict__map[key] = [last, root, key]
else:
    OrderedDictEx = OrderedDict


def lru_cache(maxsize=100):
    """Least-recently-used cache decorator.

    If *maxsize* is set to None, the LRU features are disabled and the cache
    can grow without bound.

    Arguments to the cached function must be hashable.

    View the cache statistics named tuple (hits, misses, maxsize, currsize) with
    f.cache_info().  Clear the cache and statistics with f.cache_clear().
    Access the underlying function with f.__wrapped__.

    See:  http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used

    """

    # Users should only access the lru_cache through its public API:
    #       cache_info, cache_clear, and f.__wrapped__
    # The internals of the lru_cache are encapsulated for thread safety and
    # to allow the implementation to change (including a possible C version).

    def decorating_function(user_function,
                            tuple=tuple, sorted=sorted, len=len, KeyError=KeyError):

        hits, misses = [0], [0]
        kwd_mark = (object(),)  # separates positional and keyword args
        lock = Lock()  # needed because OrderedDict isn't threadsafe

        if maxsize is None:
            cache = dict()  # simple cache without ordering or size limit

            @wraps(user_function)
            def wrapper(*args, **kwds):
                key = args
                if kwds:
                    key += kwd_mark + tuple(sorted(kwds.items()))
                try:
                    result = cache[key]
                    hits[0] += 1
                    return result
                except KeyError:
                    pass
                result = user_function(*args, **kwds)
                cache[key] = result
                misses[0] += 1
                return result
        else:
            cache = OrderedDictEx()  # ordered least recent to most recent
            cache_popitem = cache.popitem
            cache_renew = cache.move_to_end

            @wraps(user_function)
            def wrapper(*args, **kwds):
                key = args
                if kwds:
                    key += kwd_mark + tuple(sorted(kwds.items()))
                with lock:
                    try:
                        result = cache[key]
                        cache_renew(key)  # record recent use of this key
                        hits[0] += 1
                        return result
                    except KeyError:
                        pass
                result = user_function(*args, **kwds)
                with lock:
                    cache[key] = result  # record recent use of this key
                    misses[0] += 1
                    if len(cache) > maxsize:
                        cache_popitem(0)  # purge least recently used cache entry
                return result

        def cache_info():
            """Report cache statistics"""
            with lock:
                return _CacheInfo(hits[0], misses[0], maxsize, len(cache))

        def cache_clear():
            """Clear the cache and cache statistics"""
            with lock:
                cache.clear()
                hits[0] = misses[0] = 0

        wrapper.cache_info = cache_info
        wrapper.cache_clear = cache_clear
        return wrapper

    return decorating_function


def memoize(fn):
    '''
    Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''
    cache = fn.cache = {}
    fn.invalidate_cache = lambda: cache.clear()

    @functools.wraps(fn)
    def _memoized(*args, **kwargs):
        kwargs.update(dict(zip(getargspec(fn).args, args)))
        key = tuple(kwargs.get(k, None) for k in getargspec(fn).args if k != 'self')
        if not isinstance(key, Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return fn(**kwargs)
        if key not in cache:
            cache[key] = fn(**kwargs)
        return cache[key]

    return _memoized


def memoize_in_object(fn):
    """
    Decorator. Caches a method's return value each time it is called, in the object instance
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    """

    fn.cache = {}

    @functools.wraps(fn)
    def _memoize(self, *args, **kwargs):
        cache = fn.cache.setdefault(self, {})
        kwargs.update(dict(zip(getargspec(fn).args, itertools.chain([self], args))))
        key = tuple(kwargs.get(k, None) for k in getargspec(fn).args if k != 'self')
        if not isinstance(key, Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return fn(**kwargs)
        if key not in cache:
            cache[key] = fn(**kwargs)
        return cache[key]

    return _memoize


bytes_types = (bytes, bytearray)


def incr_last_byte(data):
    """
    Get the last byte in the array and increment it
    """
    if not isinstance(data, bytes_types):
        if isinstance(data, six.string_types):
            data = data.encode('utf-8')
        else:
            data = six.b(str(data))
    s = bytearray(data)
    s[-1] = s[-1] + 1
    return bytes(s)


def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


def check_param(at_least_one_of=None, at_most_one_of=None):
    """
    check if at least/most one of params is given

    >>> @check_param(at_least_one_of=['a', 'b'])
    >>> def fn(a=None, b=None):
    ...     pass
    >>> fn()
    TypeError: fn() requires at least one argument of a,b
    """

    def deco(fn):
        if not (at_least_one_of or at_most_one_of):
            raise TypeError("check_param() requires at least one argument of at_least_one_of, at_most_one_of")
        if not (isinstance(at_least_one_of, (list, tuple)) or isinstance(at_most_one_of, (list, tuple))):
            raise TypeError("check_param() only accept list or tuple as parameter")

        @functools.wraps(fn)
        def inner(*args, **kwargs):
            arguments = merge_two_dicts(kwargs, dict(zip(getargspec(fn).args, args)))
            if at_least_one_of and not [arguments.get(i) for i in at_least_one_of if arguments.get(i) is not None]:
                raise TypeError("{name}() requires at least one argument of {args}"
                                .format(name=fn.__name__, args=','.join(at_least_one_of)))
            if at_most_one_of:
                if len([arguments.get(i) for i in at_most_one_of if arguments.get(i) is not None]) > 1:
                    raise TypeError("{name}() requires at most one of param {args}"
                                    .format(name=fn.__name__, args=' or '.join(at_most_one_of)))
            return fn(*args, **kwargs)

        return inner

    return deco


def run_coro(coro):
    """
    :type coro: asyncio.coroutine
    :param coro: the coroutine to run
    """
    import asyncio

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


class cached_property(object):
    """A property that is only computed once per instance and then replaces
       itself with an ordinary attribute. Deleting the attribute resets the
       property.

       Source: https://github.com/bottlepy/bottle/blob/0.11.5/bottle.py#L175
    """

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            # We're being accessed from the class itself, not from an object
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


_lb = b'{'
_rb = b'}'
if six.PY3:
    _lb = ord(_lb)
    _rb = ord(_rb)


def iter_json_string(chunk, start=0, lb=_lb, rb=_rb, resp=None, err_cls=ValueError):
    last_i = 0
    bracket_flag = 0
    for i, c in enumerate(chunk, start=start):
        if c == lb:  # b'{'
            bracket_flag += 1
        elif c == rb:  # b'}'
            bracket_flag -= 1
        if bracket_flag == 0:
            s = chunk[last_i:i + 1]
            last_i = i + 1
            yield True, s, i
        elif bracket_flag < 0:
            raise err_cls("Stream decode error", chunk, resp)
    yield False, chunk[last_i:], last_i - 1
