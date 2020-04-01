from collections import namedtuple, OrderedDict

import enum
import functools
import itertools
import logging
import os
import shlex
import sys
import time
import warnings
from subprocess import Popen, PIPE
from threading import Lock

try:  # pragma: no cover
    from collections.abc import Hashable
except ImportError:
    try:
        from typing import Hashable
    except ImportError:
        from collections import Hashable

try:  # pragma: no cover
    from threading import get_ident
except ImportError:
    from thread import get_ident

try:  # pragma: no cover
    from inspect import getfullargspec as getargspec
except ImportError:  # pragma: no cover
    from inspect import getargspec
import six
from six import wraps

_CacheInfo = namedtuple("CacheInfo", "hits misses maxsize currsize")

if six.PY2:
    class OrderedDictEx(OrderedDict):  # pragma: no cover
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

log = logging.getLogger('etcd3')


def lru_cache(maxsize=100):  # pragma: no cover
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


def memoize(fn):  # pragma: no cover
    '''
    Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''
    cache = fn.cache = {}
    fn.invalidate_cache = lambda: cache.clear()
    fnargs = getargspec(fn).args

    @functools.wraps(fn)
    def _memoized(*args, **kwargs):
        kwargs.update(dict(zip(fnargs, args)))
        key = tuple(kwargs.get(k, None) for k in fnargs if k != 'self')
        if not isinstance(key, Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return fn(**kwargs)
        if key not in cache:
            cache[key] = fn(**kwargs)
        return cache[key]

    return _memoized


def memoize_in_object(fn):  # pragma: no cover
    """
    Decorator. Caches a method's return value each time it is called, in the object instance
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    """

    fn.cache = {}
    fnargs = getargspec(fn).args

    @functools.wraps(fn)
    def _memoize(self, *args, **kwargs):
        cache = fn.cache.setdefault(self, {})
        kwargs.update(dict(zip(fnargs, itertools.chain([self], args))))
        key = tuple(kwargs.get(k, None) for k in fnargs if k != 'self')
        if not isinstance(key, Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return fn(**kwargs)
        if key not in cache:
            cache[key] = fn(**kwargs)
        return cache[key]

    return _memoize


bytes_types = (bytes, bytearray)


def incr_last_byte(data):  # pragma: no cover
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


def check_param(at_least_one_of=None, at_most_one_of=None):  # pragma: no cover
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
        fnargs = getargspec(fn).args

        def raise_if_not_at_least_one(arguments):
            if not any(arguments.get(i) != None for i in at_least_one_of):
                raise TypeError("{name}() requires at least one argument of {args}"
                                .format(name=fn.__name__, args=','.join(at_least_one_of)))

        def raise_if_more_than_one(arguments):
            if len([arguments.get(i) for i in at_most_one_of if arguments.get(i) is not None]) > 1:
                raise TypeError("{name}() requires at most one of param {args}"
                                .format(name=fn.__name__, args=' or '.join(at_most_one_of)))

        @functools.wraps(fn)
        def at_least_one(*args, **kwargs):
            arguments = merge_two_dicts(kwargs, dict(zip(fnargs, args)))
            raise_if_not_at_least_one(arguments)
            return fn(*args, **kwargs)

        @functools.wraps(fn)
        def at_most_one(*args, **kwargs):
            arguments = merge_two_dicts(kwargs, dict(zip(fnargs, args)))
            raise_if_more_than_one(arguments)
            return fn(*args, **kwargs)

        @functools.wraps(fn)
        def both(*args, **kwargs):
            arguments = merge_two_dicts(kwargs, dict(zip(fnargs, args)))
            raise_if_not_at_least_one(arguments)
            raise_if_more_than_one(arguments)
            return fn(*args, **kwargs)

        if at_least_one_of and not at_most_one_of:
            return at_least_one
        elif at_most_one_of and not at_least_one_of:
            return at_most_one
        else:
            return both

    return deco


def run_coro(coro):  # pragma: no cover
    """
    :type coro: asyncio.coroutine
    :param coro: the coroutine to run
    """
    import asyncio

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


class cached_property(object):  # pragma: no cover
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
if six.PY3:  # pragma: no cover
    _lb = ord(_lb)
    _rb = ord(_rb)


def iter_json_string(chunk, start=0, lb=_lb, rb=_rb, resp=None, err_cls=ValueError):
    last_i = 0
    bracket_flag = 0
    # hack to improve performance
    if chunk.startswith(b'{"result":') and chunk[-1] == rb and chunk.count(b'{"result":') == 1:
        last_i = len(chunk)
        yield True, chunk, 0
    else:
        for i, c in enumerate(chunk, start=start):
            if c == lb:  # b'{'
                bracket_flag += 1
            elif c == rb:  # b'}'
                bracket_flag -= 1
            if bracket_flag == 0:
                s = chunk[last_i:i + 1]
                last_i = i + 1
                yield True, s, i
            elif bracket_flag < 0:  # pragma: no cover
                raise err_cls("Stream decode error", chunk, resp)
    yield False, chunk[last_i:], last_i - 1


def enum_value(e):  # pragma: no cover
    if isinstance(e, enum.Enum):
        return e.value
    return e


def retry(func, max_tries=3, log=logging, err_cls=Exception):  # pragma: no cover
    i = 1
    while True:
        try:
            time.sleep(0.3)
            func()
            break
        except err_cls as e:
            if i < max_tries:
                log.debug("%s() failed (times:%d) retrying %s" % (func.__name__, i, e))
                i += 1
            else:
                raise


def exec_cmd(cmd, envs=None, raise_error=True):  # pragma: no cover
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    envs = envs or {}
    cmd = cmd[:]
    exe = find_executable(cmd[0])
    if exe:
        cmd[0] = exe
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, env=envs)
    out, err = p.communicate()
    if p.returncode != 0 and raise_error:
        raise RuntimeError(err)
    return out


class Etcd3Warning(UserWarning):
    pass


warnings.simplefilter('always', Etcd3Warning)


# https://gist.github.com/4368898
# Public domain code by anatoly techtonik <techtonik@gmail.com>
# AKA Linux `which` and Windows `where`
def find_executable(executable, path=None):  # pragma: no cover
    """Find if 'executable' can be run. Looks for it in 'path'
    (string that lists directories separated by 'os.pathsep';
    defaults to os.environ['PATH']). Checks for all executable
    extensions. Returns full path or None if no command is found.
    """
    if path is None:
        path = os.environ['PATH']
    paths = path.split(os.pathsep)
    extlist = ['']
    if os.name == 'os2':
        (base, ext) = os.path.splitext(executable)
        # executable files on OS/2 can have an arbitrary extension, but
        # .exe is automatically appended if no dot is present in the name
        if not ext:
            executable = executable + ".exe"
    elif sys.platform == 'win32':
        pathext = os.environ['PATHEXT'].lower().split(os.pathsep)
        (base, ext) = os.path.splitext(executable)
        if ext.lower() not in pathext:
            extlist = pathext
    for ext in extlist:
        execname = executable + ext
        if os.path.isfile(execname):
            return execname
        else:
            for p in paths:
                f = os.path.join(p, execname)
                if os.path.isfile(f):
                    return f
        # violent fix of my wired test environment
        for p in ['/usr/local/bin']:
            f = os.path.join(p, execname)
            if os.path.isfile(f):
                return f
