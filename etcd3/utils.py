import functools
import itertools
from collections import namedtuple, OrderedDict, Hashable
from inspect import getargspec
from threading import Lock

import six
from six import wraps

bytes_types = (bytes, bytearray)

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


if __name__ == '__main__':
    @lru_cache(maxsize=2)
    def f(a):
        print('calc:%s' % a)
        return a ** 2


    for i in range(1, 20):
        print(f(i % 3))
