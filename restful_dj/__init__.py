from django.urls import path

from . import router

from .router import set_before_dispatch_handler

from .util import collector

urls = (
    [
        path('<str:entry>', router.dispatch),
        path('<str:entry>/<str:name>', router.dispatch)
    ],
    router.NAME,
    router.NAME
)
