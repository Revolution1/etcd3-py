from collections import namedtuple, OrderedDict
from threading import Lock

import six
from six import wraps

bytes_types = (bytes, bytearray)

_CacheInfo = namedtuple("CacheInfo", "hits misses maxsize currsize")

if six.PY2:
    class OrderedDictEx(OrderedDict):
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


if __name__ == '__main__':
    @lru_cache(maxsize=2)
    def f(a):
        print('calc:%s' % a)
        return a ** 2
    for i in range(1, 20):
        print(f(i % 3))
