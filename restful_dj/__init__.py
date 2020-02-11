from django.urls import path

from . import router

from .util import collector

urls = (
    [
        path('<str:entry>', router.dispatch),
        path('<str:entry>/<str:name>', router.dispatch)
    ],
    router.NAME,
    router.NAME
)
