import os

from django.conf import settings
from django.http import HttpResponse, HttpRequest

from .meta import RouteMeta
from .util import logger

# 注册的路由中间件列表
from .util.utils import load_module

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

    middleware = getattr(module, class_name)

    if middleware not in MIDDLEWARE_INSTANCE_LIST:
        MIDDLEWARE_INSTANCE_LIST.append(middleware())

    return True


class MiddlewareBase:
    """
    路由中间件基类
    """

    def __init__(self):
        self.session = {}

    def request_process(self, request, meta: RouteMeta, **kwargs):
        """
        对 request 对象进行预处理。一般用于请求的数据的解码
        :param request:
        :param meta:
        :param kwargs:
        :return: 返回 HttpResponse 以终止请求
        """
        pass

    def response_process(self, request, meta: RouteMeta, **kwargs):
        """
        对 response 数据进行预处理。一般用于响应的数据的编码
        :rtype: HttpResponse
        :param meta:
        :param request:
        :param kwargs: 始终会有一个 'response' 的项，表示返回的 HttpResponse
        :return: 应该始终返回一个  HttpResponse
        """
        assert 'response' in kwargs
        return kwargs['response']

    def check_login_status(self, request, meta: RouteMeta, **kwargs):
        """
        检查用户的登录状态，使用时请覆写此方法
        :rtype: bool | HttpResponse
        :param request:
        :param meta:
        :param kwargs:
        :return: True|False|HttpResponse 已经登录时返回 True，否则返回 False，HttpResponse 响应
        """
        return True

    def check_user_permission(self, request, meta: RouteMeta, **kwargs):
        """
        检查用户是否有权限访问此路由，使用时请覆写此方法
        :rtype: bool | HttpResponse
        :param request:
        :param meta:
        :param kwargs:
        :return: True|False|HttpResponse 已经登录时返回 True，否则返回 False，HttpResponse 响应
        """
        return True

    def check_params(self, request, meta: RouteMeta, **kwargs):
        """
        在调用路由函数前，对参数进行处理，使用时请覆写此方法
        :param request:
        :param meta:
        :param kwargs:
        :return: 返回 HttpResponse 以终止请求
        """
        pass

    def process_return_value(self, request, meta: RouteMeta, **kwargs):
        """
        在路由函数调用后，对其返回值进行处理
        :param request:
        :param meta:
        :param kwargs: 始终会有一个 'data' 的项，表示返回的原始数据
        :return: 返回 HttpResponse 以终止执行
        """
        assert 'data' in kwargs
        return kwargs['data']


class MiddlewareManager:
    """
    路由中间件管理器
    """

    def __init__(self, request: HttpRequest, meta: RouteMeta):
        # HTTP请求对象
        self.request = request
        # 元数据信息
        self.meta = meta

    def invoke(self):
        # 对 request 进行预处理
        for middleware in MIDDLEWARE_INSTANCE_LIST:
            if not hasattr(middleware, 'request_process'):
                continue
            result = middleware.request_process(self.request, self.meta)
            if isinstance(result, HttpResponse):
                return result

        # 不需要登录，也不需要检查用户权限
        if not self.meta.permission:
            return True

        # 需要检查登录状态
        for middleware in MIDDLEWARE_INSTANCE_LIST:
            if not hasattr(middleware, 'check_login_status'):
                continue

            result = middleware.check_login_status(self.request, self.meta)

            # 没有返回结果
            if result is None:
                continue

            # 如果路由中间件有返回结果
            if isinstance(result, HttpResponse):
                return result

            # 只要不返回 true 都表示不能继续了
            if result is False:
                return result

        # 需要检查用户权限
        for middleware in MIDDLEWARE_INSTANCE_LIST:
            if self.meta.permission and hasattr(middleware, 'check_user_permission'):
                result = middleware.check_user_permission(self.request, self.meta)

                # 没有返回结果
                if result is None:
                    continue

                # 如果路由中间件有返回结果
                if isinstance(result, HttpResponse):
                    return result

                # 只要不返回 true 都表示不能继续了
                if result is not True:
                    return result
        return True

    def params(self):
        """
        在调用路由函数前，对参数进行处理
        :param request:
        :return:
        """
        # 对 response 进行处理
        for middleware in MIDDLEWARE_INSTANCE_LIST:
            if not hasattr(middleware, 'check_params'):
                continue
            result = middleware.check_params(self.request, self.meta)

            # 没有返回结果
            if result is None:
                continue

            # 如果路由中间件有返回结果
            if isinstance(result, HttpResponse):
                return result

    def process_return(self, data):
        """
        在路由函数调用后，对其返回值进行处理
        :param data:
        :return:
        """
        for middleware in MIDDLEWARE_INSTANCE_LIST:
            if not hasattr(middleware, 'process_return_value'):
                continue
            result = middleware.process_return_value(self.request, self.meta, data=data)

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
            if not hasattr(middleware, 'response_process'):
                continue
            response = middleware.response_process(self.request, self.meta, response=response)

        return response
