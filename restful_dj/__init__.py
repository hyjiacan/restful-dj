from django.conf import settings
from django.urls import path

from .decorator import route
from .meta import RouteMeta
from .router import set_before_dispatch_handler
from .util import collector
from .util.dot_dict import DotDict
from .util.logger import set_logger

urls = (
    [
        path('', router.render_list),
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
    'RouteMeta',
    'set_before_dispatch_handler',
    'set_logger',
    'urls'
]

if settings.DEBUG:
    settings.INSTALLED_APPS.append('restful_dj')
