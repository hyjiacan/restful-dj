import inspect
import os
from types import MethodType

from django import shortcuts
from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponseServerError, HttpRequest, HttpResponse

from .util import collector, utils
from .util import logger
from .util.utils import load_module

# 包名称
NAME = 'restful_dj'

# 函数缓存，减少 inspect 反射调用次数
ENTRY_CACHE = {}

_BEFORE_DISPATCH_HANDLER = None

# 线上模式时，使用固定路由
PRODUCTION_ROUTES = {}

# 开发模式的模块缓存，用于API列表
MODULES_CACHE = None

# 路由映射表，其键为请求的路径，其值为映射的目录
ROUTES_MAP = {}


def map_routes(routes_map: dict):
    """
    注册路由映射表
    :param routes_map:
    :return:
    """
    for path in routes_map:
        ROUTES_MAP[path] = routes_map[path]


def register_routes(routes: list):
    """
    手动注册路由列表
    :param routes: 其每一项都应该是一个 list, 元素依次为 method: str, path: str, handler: MethodType
    :return:
    """
    for _route in routes:
        register(*_route)


def register(method: str, path: str, handler: MethodType):
    """
    手动注册路由
    :param path:
    :param method:
    :param handler:
    :return:
    """
    rid = '%s#%s' % (path, method.lower())
    if rid in PRODUCTION_ROUTES:
        logger.warning('[restful-dj] %s %s exists' % (method, path))

    args = utils.get_func_args(handler)
    PRODUCTION_ROUTES[rid] = {
        'func': handler,
        'args': args
    }


def set_before_dispatch_handler(handler):
    """
    设置请求分发前的处理函数
    :param handler:
    :return:
    """
    global _BEFORE_DISPATCH_HANDLER
    _BEFORE_DISPATCH_HANDLER = handler


# noinspection PyUnusedLocal
def redirect(request, entry, name=''):
    """
    当请求的URL使用了 / 结尾时，重定向到不使用 / 结尾的地址
    :param request:
    :param entry:
    :param name:
    :return:
    """
    return shortcuts.redirect(request.path.rstrip('/'))


def render_list(request):
    if not settings.DEBUG:
        return HttpResponseNotFound()

    global MODULES_CACHE

    prefix = '%s://%s%s' % (request.scheme, request.META.get('HTTP_HOST'), request.path)

    if MODULES_CACHE is None:
        routes = collector.collect()

        modules = {}

        for route in routes:
            module = route['module']

            p = route['path']
            suffix = ''
            temp = p.split('/')
            entry = temp[0]
            if len(temp) == 2:
                suffix = temp[1]

            router = Router(request, route['method'], entry, suffix)
            router.check()
            define = router.get_func_define()
            if define and len(define['args']) > 0:
                route['args'] = [define['args'][arg] for arg in define['args']]
            else:
                route['args'] = None

            if module in modules:
                modules[module].append(route)
            else:
                modules[module] = [route]
        MODULES_CACHE = modules

    return shortcuts.render(request, 'restful_dj_api_list_template.html', {
        'modules': MODULES_CACHE,
        'prefix': prefix
    })


def dispatch(request, entry, name=''):
    """
    REST-ful 路由分发入口
    :param request: 请求
    :param entry: 入口文件，包名使用 . 符号分隔
    :param name='' 指定的函数名称
    :return:
    """
    if _BEFORE_DISPATCH_HANDLER is not None:
        # noinspection PyCallingNonCallable
        entry, name = _BEFORE_DISPATCH_HANDLER(request, entry, name)

    if not settings.DEBUG:
        return _route_for_production(request, entry, name)

    router = Router(request, request.method, entry, name)
    check_result = router.check()
    if isinstance(check_result, HttpResponse):
        return check_result
    return router.route()


def _route_for_production(request, entry, name):
    method = request.method.lower()
    # noinspection PyBroadException
    try:
        if name == '':
            route = PRODUCTION_ROUTES['%s#%s' % (entry, method)]
        else:
            route = PRODUCTION_ROUTES['%s/%s#%s' % (entry, name, method)]
    except Exception:
        return HttpResponseNotFound()

    return _invoke_handler(request, route['func'], route['args'])


def _invoke_handler(request, func, args):
    try:
        return func(request, args)
    except Exception as e:
        message = '[restful-dj]\n\t%s' % utils.get_func_info(func)
        logger.error(message, e)
        return HttpResponseServerError('%s: %s' % (message, str(e)))


class Router:
    def __init__(self, request: HttpRequest, method: str, entry: str, name: str):
        self.request = request
        self.entry = entry
        method = method.lower()
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
            logger.info(message)
            return HttpResponseNotFound()

        if func_define is HttpResponse:
            return func_define

        return _invoke_handler(self.request, func_define['func'], func_define['args'])

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
            entry_define = load_module(module_name)
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
            msg = '%s\n\tDecorator "@route" not found on function "%s", did you forgot it ?' % (
                utils.get_func_info(func),
                fullname
            )
            logger.warning(msg)
            # 没有配置装饰器@route，则认为函数不可访问，更新缓存
            ENTRY_CACHE[func_name] = False
            return False

        ENTRY_CACHE[fullname] = {
            'func': func,
            # 该函数的参数列表
            # 'name': {
            #     'annotation': '类型', 当未指定类型时，无此项
            #     'default': '默认值'，当未指定默认值时，无此项
            # }
            'args': utils.get_func_args(func)
        }

        return ENTRY_CACHE[fullname]

    @staticmethod
    def is_valid_route(func):
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

    @staticmethod
    def get_route_map(route_path):
        # 命中
        hit_route = None
        for root_path in ROUTES_MAP:
            if route_path.startswith(root_path):
                hit_route = root_path, ROUTES_MAP[root_path]
                break

        if hit_route is None:
            return None

        # 将请求路径替换为指定的映射路径
        return ('%s%s' % (hit_route[1], route_path[len(hit_route[0]):])).strip('.')
