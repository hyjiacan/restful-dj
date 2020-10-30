from .decorator import route
from .meta import RouteMeta
from .middleware import register_middlewares
from .router import set_before_dispatch_handler, register_routes, map_routes
from .util.collector import collect, persist, register_globals
from .util.logger import set_logger


def _initialize():
    from django.conf import settings
    from django.urls import path

    from . import router

    _routes = [
        path('<str:entry>', router.dispatch),
        path('<str:entry>/', router.redirect),
        path('<str:entry>/<str:name>', router.dispatch),
        path('<str:entry>/<str:name>/', router.redirect)
    ]

    if settings.DEBUG:
        from . import apis

        apis.register_template_dir()
        _routes.insert(0, path('', apis.render), )

    return (
        _routes,
        router.NAME,
        router.NAME
    )


dispatch = _initialize()

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
