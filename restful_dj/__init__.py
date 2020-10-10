import os

from django.conf import settings
from django.urls import path

from . import router
from .decorator import route
from .meta import RouteMeta
from .middleware import register_middlewares
from .router import set_before_dispatch_handler, register_routes, map_routes
from .util.collector import collect, persist, register_globals
from .util.logger import set_logger

dispatch = (
    [
        path('', router.render_list),
        path('<str:entry>', router.dispatch),
        path('<str:entry>/', router.redirect),
        path('<str:entry>/<str:name>', router.dispatch),
        path('<str:entry>/<str:name>/', router.redirect)
    ],
    router.NAME,
    router.NAME
)

__all__ = [
    'collect',
    'persist',
    'route',
    'RouteMeta',
    'set_before_dispatch_handler',
    'set_logger',
    'map_routes',
    'register_globals',
    'register_routes',
    'register_middlewares',
    'dispatch'
]


def register_template_dir():
    template_conf = settings.TEMPLATES[0]
    if 'DIRS' not in template_conf:
        template_conf['DIRS'] = []

    template_conf['DIRS'].append(os.path.join(os.path.dirname(__file__), 'templates'))


if settings.DEBUG:
    register_template_dir()
