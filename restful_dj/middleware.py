import os

from django.conf import settings
from django.http import HttpResponse

from .util import logger

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

    module = __import__(module_name, fromlist=True)

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

    def request_process(self, request):
        """
        对 request 对象进行预处理。一般用于请求的数据的解码
        :param request:
        :return: 返回 HttpResponse 以终止请求
        """
        pass

    def response_process(self, request, response):
        """
        对 response 数据进行预处理。一般用于响应的数据的编码
        :param request:
        :param response:
        :return:
        """
        pass

    def check_login_status(self, request, meta):
        """
        检查用户的登录状态，使用时请覆写此方法
        :param request:
        :param meta:
        :return: True|False|HttpResponse 已经登录时返回 True，否则返回 False，HttpResponse 响应
        """
        return True

    def check_user_permission(self, request, meta):
        """
        检查用户是否有权限访问此路由，使用时请覆写此方法
        :param request:
        :param meta:
        :return: True|False|HttpResponse 已经登录时返回 True，否则返回 False，HttpResponse 响应
        """
        return True


class MiddlewareManager:
    """
    路由中间件管理器
    """

    def __init__(self):
        # 处理函数的id
        self.id = None
        # 处理函数的名称
        self.handler = None
        # 路由模块名称
        self.module = None
        # 路由名称
        self.name = None
        # 是否需要用户权限
        self.permission_required = True
        # HTTP请求对象
        self.request = None

    def invoke(self):
        # 对 request 进行预处理
        for middleware in MIDDLEWARE_INSTANCE_LIST:
            if not hasattr(middleware, 'request_process'):
                continue
            result = middleware.request_process(self.request)
            if isinstance(result, HttpResponse):
                return result

        # 不需要登录，也不需要检查用户权限
        if not self.permission_required:
            return True

        # 需要检查登录状态
        for middleware in MIDDLEWARE_INSTANCE_LIST:
            if not hasattr(middleware, 'check_login_status'):
                continue

            result = middleware.check_login_status(self.request, {
                'id': self.id,
                'handler': self.handler,
                'module': self.module,
                'name': self.name
            })

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
            if self.permission_required and hasattr(middleware, 'check_user_permission'):
                result = middleware.check_user_permission(self.request, {
                    'id': self.id,
                    'handler': self.handler,
                    'module': self.module,
                    'name': self.name
                })

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
            response = middleware.response_process(self.request, response)

        return response
