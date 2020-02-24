import inspect
import os
from collections import OrderedDict

from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponseServerError, HttpRequest, HttpResponse

from .middleware import add_middleware
from .util import logger

# 包名称
from .util.dot_dict import DotDict

NAME = 'restful_dj'

APP_CONFIG_KEY = 'RESTFUL_DJ'
APP_CONFIG_ROUTE = 'routes'
APP_CONFIG_MIDDLEWARE = 'middleware'
APP_CONFIG_LOGGER = 'logger'

if not hasattr(settings, APP_CONFIG_KEY):
    print('config item not found in settings.py: %s' % APP_CONFIG_KEY)
    exit(1)

# 已注册APP集合
CONFIG_ROOT: dict = getattr(settings, APP_CONFIG_KEY)

if APP_CONFIG_ROUTE not in CONFIG_ROOT:
    print('config item not found in settings.py!%s: %s' % (APP_CONFIG_KEY, APP_CONFIG_ROUTE))
    exit(1)

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

# 函数缓存，减少 inspect 反射调用次数
ENTRY_CACHE = {}

_BEFORE_DISPATCH_HANDLER = None


def set_before_dispatch_handler(handler):
    """
    设置请求分发前的处理函数
    :param handler:
    :return:
    """
    global _BEFORE_DISPATCH_HANDLER
    _BEFORE_DISPATCH_HANDLER = handler


def dispatch(request, entry, name=''):
    """
    REST-ful 路由分发入口
    :param request: 请求
    :param entry: 入口文件，包名使用 . 符号分隔
    :param name='' 指定的函数名称
    :return:
    """
    if _BEFORE_DISPATCH_HANDLER is not None:
        entry, name = _BEFORE_DISPATCH_HANDLER(request, entry, name)
    router = Router(request, entry, name)
    check_result = router.check()
    if isinstance(check_result, HttpResponse):
        return check_result
    return router.route()


class Router:
    def __init__(self, request: HttpRequest, entry: str, name: str):
        self.request = request
        self.entry = entry
        method = request.method.lower()
        self.method = method

        # 如果指定了名称，那么就加上
        # 如：name = 'detail'
        #   func_name = get_detail
        if name:
            func_name = '%s_%s' % (method, name.lower())
        else:
            func_name = method
        self.func_name = func_name

        # 处理映射
        # 对应的模块(文件路径）
        self.module_name = self.get_route_map(entry)

        self.fullname = ''

    def check(self):
        module_name = self.module_name

        if module_name is None:
            logger.warning('Cannot find route map in RESTFUL_DJ.routes: %s' % self.entry)
            return HttpResponseNotFound()

        # 如果 module_name 是目录，那么就查找 __init__.py 是否存在
        abs_path = os.path.join(settings.BASE_DIR, module_name.replace('.', os.path.sep))
        if os.path.isdir(abs_path):
            logger.info('Entry "%s" is package, auto load module "__init__.py"' % module_name)
            module_name = '%s.%s' % (module_name, '__init__')
        elif not os.path.exists('%s.py' % abs_path):
            return HttpResponseNotFound()

        self.module_name = module_name

        # 完全限定名称
        self.fullname = '%s.%s' % (module_name, self.func_name)

    def route(self):
        try:
            func_define = self.get_func_define()
        except Exception as e:
            message = 'Load entry "%s" failed' % self.module_name
            logger.error(message, e)
            return HttpResponseNotFound()

        # 如果 func_define 为 False ，那就表示此函数不存在
        if func_define is False:
            message = 'Route "%s.%s" not found' % (self.module_name, self.func_name)
            logger.error(message)
            return HttpResponseNotFound()

        if func_define is HttpResponse:
            return func_define

        try:
            return func_define.func(self.request, func_define.args)
        except Exception as e:
            message = 'Router invoke exception'
            logger.error(message, e)
            return HttpResponseServerError('%s: %s' % (message, str(e)))

    def get_func_define(self):
        fullname = self.fullname
        func_name = self.func_name
        module_name = self.module_name

        # 缓存中有这个函数
        if fullname in ENTRY_CACHE.keys():
            return ENTRY_CACHE[fullname]

        # 缓存中没有这个函数，去模块中查找
        # ---------------

        try:
            # 如果不加上fromlist=True,只会导入目录
            # noinspection PyTypeChecker
            # __import__ 自带缓存
            entry_define = __import__(module_name, fromlist=True)
        except Exception as e:
            message = 'Load module "%s" failed' % module_name
            logger.error(message, e)
            return HttpResponseNotFound()

        # 模块中也没有这个函数
        if not hasattr(entry_define, func_name):
            # 函数不存在，更新缓存
            ENTRY_CACHE[func_name] = False
            return False

        # 模块中有这个函数
        # 通过反射从模块加载函数
        func = getattr(entry_define, func_name)
        if not self.is_valid_route(func):
            msg = 'Decorator "@route" not found on function "%s", did you forgot it ?' % fullname
            logger.warning(msg)
            # 没有配置装饰器@route，则认为函数不可访问，更新缓存
            ENTRY_CACHE[func_name] = False
            return False

        parameters = inspect.signature(func).parameters

        args = OrderedDict()

        for p in parameters.keys():
            spec = DotDict()
            # 类型
            annotation = parameters.get(p).annotation
            default = parameters.get(p).default
            if default != inspect._empty:
                spec['default'] = default

            # 有默认值时，若未指定类型，则使用默认值的类型
            if annotation == inspect._empty:
                if default is not None and default != inspect._empty:
                    spec['annotation'] = type(default)
            else:
                spec['annotation'] = annotation

            args[p] = spec

        ENTRY_CACHE[fullname] = DotDict({
            'func': func,
            # 该函数的参数列表
            # 'name': {
            #     'annotation': '类型', 当未指定类型时，无此项
            #     'default': '默认值'，当未指定默认值时，无此项
            # }
            'args': args
        })

        return ENTRY_CACHE[fullname]

    def is_valid_route(self, func):
        source = inspect.getsource(func)
        lines = source.split('\n')
        for line in lines:
            if line.startswith('def '):
                # 已经查找到了函数定义部分了，说明没有找到
                return False

            if line.startswith('@route('):
                # 是 @route 装饰器行
                return True
        return False

    def get_route_map(self, route_path):
        # 命中
        hit_route = None
        for root_path in CONFIG_ROUTE:
            if route_path.startswith(root_path):
                hit_route = root_path, CONFIG_ROOT[APP_CONFIG_ROUTE][root_path]
                break

        if hit_route is None:
            return None

        # 将请求路径替换为指定的映射路径
        return ('%s%s' % (hit_route[1], route_path[len(hit_route[0]):])).strip('.')
