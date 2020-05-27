import os

from django.conf import settings
from django.http import HttpResponse, HttpRequest

from .meta import RouteMeta
from .util import logger
from .util.utils import load_module

# 注册的路由中间件列表
MIDDLEWARE_INSTANCE_LIST = []


def add_middleware(middleware_name):
    """
    添加路由中间件
    :param middleware_name:中间件的模块完全限定名称
    :return:
    """

    temp = middleware_name.split('.')

    class_name = temp.pop()

    module_name = '.'.join(temp)

    module_path = os.path.join(settings.BASE_DIR, module_name.replace('.', os.path.sep))

    if not os.path.exists(module_path + '.py'):
        # 是目录 (package)，尝试使用默认的
        if os.path.exists(module_path):
            module_path = os.path.join(module_path, '__init__.py')
            module_name += '.__init__'

        if not os.path.exists(module_path):
            logger.error('Middleware for restful-dj is not found: %s' % middleware_name)
            return

    module = load_module(module_name)

    middleware_cls = getattr(module, class_name)

    if middleware_cls not in MIDDLEWARE_INSTANCE_LIST:
        MIDDLEWARE_INSTANCE_LIST.append(middleware_cls())

    return True


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class MiddlewareBase:
    """
    路由中间件基类
    """

    def process_request(self, request: HttpRequest, meta: RouteMeta, **kwargs):
        """
        对 request 对象进行预处理。一般用于请求的数据的解码，此时路由组件尚水进行请求数据的解析(B,P,G 尚不可用)
        :param request:
        :param meta:
        :return: 返回 HttpResponse 以终止请求，返回 False 以停止执行后续的中间件(表示访问未授权)，返回 None 或不返回任何值继续执行后续中间件
        """
        pass

    def process_invoke(self, request: HttpRequest, meta: RouteMeta, **kwargs):
        """
        在路由函数调用前，对其参数等进行处理，此时路由组件已经完成了请求数据的解析(B,P,G 已可用)
        此时可以对解析后的参数进行变更
        :param request:
        :param meta:
        :return: 返回 HttpResponse 以终止请求，返回 False 以停止执行后续的中间件(表示访问未授权)，返回 None 或不返回任何值继续执行后续中间件
        """
        pass

    def process_return(self, request: HttpRequest, meta: RouteMeta, **kwargs):
        """
        在路由函数调用后，对其返回值进行处理
        :param request:
        :param meta:
        :param kwargs: 始终会有一个 'data' 的项，表示路由返回的原始数据
        :return: 返回 HttpResponse 以终止执行，否则返回新的 数据
        """
        assert 'data' in kwargs
        return kwargs['data']

    def process_response(self, request: HttpRequest, meta: RouteMeta, **kwargs) -> HttpResponse:
        """
        对 response 数据进行预处理。一般用于响应的数据的编码
        :param request:
        :param meta:
        :param kwargs: 始终会有一个 'response' 的项，表示路由返回的原始 HttpResponse
        :return: 无论何种情况，应该始终返回一个  HttpResponse
        :rtype: HttpResponse
        """
        assert 'response' in kwargs
        return kwargs['response']


class MiddlewareManager:
    """
    路由中间件管理器
    """

    def __init__(self, request: HttpRequest, meta: RouteMeta):
        # HTTP请求对象
        self.request = request
        # 元数据信息
        self.meta = meta

    def begin(self):
        for middleware in MIDDLEWARE_INSTANCE_LIST:
            if not hasattr(middleware, 'process_request'):
                continue
            result = middleware.process_request(self.request, self.meta)
            if isinstance(result, HttpResponse):
                return result
            # 返回 False 以阻止后续中间件执行
            if result is False:
                return

    def before_invoke(self):
        """
        在路由函数调用前，对其参数等进行处理
        :return:
        """
        for middleware in MIDDLEWARE_INSTANCE_LIST:
            if not hasattr(middleware, 'process_invoke'):
                continue
            result = middleware.process_invoke(self.request, self.meta)
            if isinstance(result, HttpResponse):
                return result
            # 返回 False 以阻止后续中间件执行
            if result is False:
                return

    def process_return(self, data):
        """
        在路由函数调用后，对其返回值进行处理
        :param data:
        :return:
        """
        for middleware in MIDDLEWARE_INSTANCE_LIST:
            if not hasattr(middleware, 'process_return'):
                continue
            result = middleware.process_return(self.request, self.meta, data=data)

            # 返回 HttpResponse 终止
            if result is HttpResponse:
                return result

            # 使用原数据
            data = result

        return data

    def end(self, response):
        """
        在响应前，对响应的数据进行处理
        :param response:
        :return:
        """
        # 对 response 进行处理
        for middleware in MIDDLEWARE_INSTANCE_LIST:
            if not hasattr(middleware, 'process_response'):
                continue
            response = middleware.process_response(self.request, self.meta, response=response)

        return response
