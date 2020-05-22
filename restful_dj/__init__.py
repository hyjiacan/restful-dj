from django.urls import path

from .decorator import route
from .meta import RouteMeta
from .router import dispatch, NAME, set_before_dispatch_handler
from .util import collector
from .util.dot_dict import DotDict
from .util.logger import set_logger

urls = (
    [
        path('<str:entry>', dispatch),
        path('<str:entry>/<str:name>', dispatch)
    ],
    NAME,
    NAME
)

__all__ = [
    'collector',
    'DotDict',
    'route',
    'RouteMeta',
    'RouteMeta',
    'set_before_dispatch_handler',
    'set_logger',
    'urls'
]
