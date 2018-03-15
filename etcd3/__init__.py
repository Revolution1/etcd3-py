# -*- coding: utf-8 -*-
# flake8: noqa
"""Top-level package for etcd3-py."""
import six

from .version import __version__, __author__, __email__

__all__ = ['__version__', '__author__', '__email__']

from .client import Client

AioClient = None
if six.PY3:
    from .aio_client import AioClient

__all__.extend([
    'Client',
    'AioClient'
])
