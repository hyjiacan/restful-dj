from django.conf import settings

from .util import logger

from .middleware import add_middleware

APP_CONFIG_KEY = 'RESTFUL_DJ'
APP_CONFIG_ROUTE = 'routes'
APP_CONFIG_MIDDLEWARE = 'middleware'
APP_CONFIG_LOGGER = 'logger'

if not hasattr(settings, APP_CONFIG_KEY):
    logger.error('config item not found in settings.py: %s' % APP_CONFIG_KEY)

# 已注册APP集合
CONFIG_ROOT: dict = getattr(settings, APP_CONFIG_KEY)

if APP_CONFIG_ROUTE not in CONFIG_ROOT:
    logger.error('config item not found in settings.py!%s: %s' % (APP_CONFIG_KEY, APP_CONFIG_ROUTE))

CONFIG_ROUTE: list = []
for _ in CONFIG_ROOT[APP_CONFIG_ROUTE].keys():
    CONFIG_ROUTE.append(_)
CONFIG_ROUTE = sorted(CONFIG_ROUTE, key=lambda i: len(i), reverse=True)

if APP_CONFIG_MIDDLEWARE in CONFIG_ROOT:
    for middleware in CONFIG_ROOT[APP_CONFIG_MIDDLEWARE]:
        add_middleware(middleware)

if APP_CONFIG_LOGGER in CONFIG_ROOT:
    custom_logger_name = CONFIG_ROOT[APP_CONFIG_MIDDLEWARE]
    logger.set_logger(__import__(custom_logger_name, fromlist=True))
