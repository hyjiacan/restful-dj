from django.conf import settings

from restful_dj.middleware import add_middleware
from restful_dj.util import logger
from restful_dj.util.utils import load_module

APP_CONFIG_KEY = 'RESTFUL_DJ'
APP_CONFIG_ROUTE = 'routes'
APP_CONFIG_MIDDLEWARE = 'middleware'
APP_CONFIG_LOGGER = 'logger'
APP_CONFIG_GLOBAL_CLASS = 'global_class'

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
    logger.set_logger(load_module(custom_logger_name))

# 全局类列表
GLOBAL_CLASSES = []
if APP_CONFIG_GLOBAL_CLASS in CONFIG_ROOT:
    for cls_path in CONFIG_ROOT[APP_CONFIG_GLOBAL_CLASS]:
        temp = cls_path.split('.')
        pkg = '.'.join(temp[0:-1])
        cls_name = temp[-1]

        GLOBAL_CLASSES.append(getattr(load_module(pkg), cls_name))
