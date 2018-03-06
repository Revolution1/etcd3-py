# -*- coding: utf-8 -*-

"""Top-level package for etcd3-py."""
from .version import __version__, __author__, __email__

__all__ = ['__version__', '__author__', '__email__']

from .client import Client

__all__.extend([
    'Client'
])
