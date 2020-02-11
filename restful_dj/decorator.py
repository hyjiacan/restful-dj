import json
from functools import wraps

from django.http import HttpResponse, JsonResponse

from .middleware import MiddlewareManager
from .util.dot_dict import DotDict

from .util import logger


def route(module=None, name=None, permission=True, ajax=True, referer=None, **kwargs):
    """
    用于控制路由的访问权限，路由均需要添加此装饰器，若未添加，则不可访问
    :param module: str 路由所属模块，一般在查询权限时会用到
    :param name: str 路由名称，一般在查询权限时会用到
    :param permission: bool 访问此地址是否需要检查用户权限,由数据库实际值控制,在这里只起到做入库作用
    :param ajax: bool 是否仅允许ajax请求,由数据库实际值控制,在这里只起到做入库作用
    :param referer: list|str 允许的来源页,由数据库实际值控制,在这里只起到做入库作用
    用法：
    @route('用户管理', '编辑用户', permission=True)
    def get(req):
        pass
    """

    def invoke_route(func):
        @wraps(func)
        def caller(request, args):
            func_name = func.__name__

            mgr = MiddlewareManager()
            mgr.id = '{0}_{1}'.format(func.__module__.replace('_', '__').replace('.', '_'), func_name)
            mgr.handler = func_name
            mgr.module = module
            mgr.name = name
            mgr.permission_required = permission
            mgr.request = request

            # 调用中间件以检查登录状态以及用户权限
            result = mgr.invoke()

            # 返回了 HttpResponse ， 直接返回此对象
            if isinstance(result, HttpResponse):
                return result

            # 返回了 False，表示未授权访问
            if result is False:
                return HttpResponseUnauthorized()

            # 处理请求中的json参数
            # 处理后可能会在 request 上添加一个 json 的项，此项存放着json格式的 body 内容
            _handle_json_params(request)

            # 调用路由处理函数
            arg_len = len(args)
            method = request.method.lower()
            if arg_len == 0:
                return func()

            if arg_len == 1:
                return func(request)

            # 多个参数，自动从 queryString, POST 或 json 中获取
            # 匹配参数

            actual_args = [request]

            # 规定：第一个参数只能是  request，所以此处直接跳过第一个参数
            position = 0
            for arg_name in args.keys():
                position += 1
                if position == 1:
                    continue

                arg_spec = args.get(arg_name)

                if method in ['delete', 'get']:
                    val = _get_arg_from_get(request, arg_name, arg_spec)
                    actual_args.append(val)
                    continue

                val = _get_arg_from_post(request, arg_name, arg_spec)
                actual_args.append(val)

            result = func(*actual_args)

            return _wrap_http_response(mgr.end(result))

        return caller

    return invoke_route


def _handle_json_params(request):
    """
    参数处理
    :return:
    """
    request.JSON = DotDict()

    if request.content_type != 'application/json':
        request.GET = DotDict(request.GET)
        request.POST = DotDict(request.POST)
        return

    # 如果请求是json类型，就先处理一下

    body = request.body

    if body == '' or body is None:
        return

    try:
        if body is str:
            request.JSON = DotDict(json.loads(body))
        elif body is dict or body is list:
            request.JSON = body
    except Exception as e:
        logger.warning('Deserialize request body fail: %s' % str(e))


def _get_arg_from_get(request, arg_name, arg_spec):
    if arg_name not in request.GET:
        if 'default' in arg_spec:
            return arg_spec.default

        # 缺少无默认值的参数
        logger.error('Missing parameter "%s"' % arg_name)
        return

    # 参数存在
    arg_value = request.GET[arg_name][0]

    if 'annotation' not in arg_spec:
        return arg_value

    # TODO 检查是否可以转换类型
    # 暂时不处理
    return arg_value


def _get_arg_from_post(request, arg_name, arg_spec):
    if arg_name not in request.POST and arg_name not in request.JSON:
        if 'default' in arg_spec:
            return arg_spec.default

        # 缺少无默认值的参数
        logger.error('Missing parameter "%s"' % arg_name)
        return

    # 参数存在
    arg_value = request.JSON[arg_name] if arg_name in request.JSON else request.POST[arg_name][0]

    if 'annotation' not in arg_spec:
        return arg_value

    # TODO 检查是否可以转换类型
    # 暂时不处理
    return arg_value


def _wrap_http_response(data):
    """
    将数据包装成 HttpResponse 返回
    :param data:
    :return:
    """
    if data is None:
        return HttpResponse()

    if isinstance(data, HttpResponse):
        return data

    if isinstance(data, bool):
        return HttpResponse('true' if bool else 'false')

    if isinstance(data, (dict, list, set, tuple, DotDict)):
        return JsonResponse(data, safe=False)

    if isinstance(data, str):
        return HttpResponse(data.encode())

    if isinstance(data, bytes):
        return HttpResponse(data)

    return HttpResponse(str(data).encode())


class HttpResponseUnauthorized(HttpResponse):
    status_code = 401
