from django.urls import path

from . import router
from .decorator import route

from .meta import RouteMeta

from .router import set_before_dispatch_handler

from .util import collector

from .util.dot_dict import DotDict

urls = (
    [
        path('<str:entry>', router.dispatch),
        path('<str:entry>/<str:name>', router.dispatch)
    ],
    router.NAME,
    router.NAME
)

__all__ = [
    'collector',
    'DotDict',
    'route',
    'RouteMeta',
    'set_before_dispatch_handler',
    'urls'
]
