import json
from functools import wraps

from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest

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
                return mgr.end(result)

            # 返回了 False，表示未授权访问
            if result is False:
                return mgr.end(HttpResponseUnauthorized())

            # 处理请求中的json参数
            # 处理后可能会在 request 上添加一个 json 的项，此项存放着json格式的 body 内容
            _process_json_params(request)

            result = mgr.params()

            # 返回了 HttpResponse ， 直接返回此对象
            if isinstance(result, HttpResponse):
                return mgr.end(result)

            # 调用路由处理函数
            arg_len = len(args)
            method = request.method.lower()
            if arg_len == 0:
                return mgr.end(_wrap_http_response(mgr, func()))

            if arg_len == 1:
                return mgr.end(_wrap_http_response(mgr, func(request)))

            # 多个参数，自动从 queryString, POST 或 json 中获取
            # 匹配参数

            actual_args = [request]

            import inspect
            signature = inspect.signature(func)

            # 规定：第一个参数只能是  request，所以此处直接跳过第一个参数
            position = 0
            for arg_name in args.keys():
                position += 1
                if position == 1:
                    continue

                arg_spec = args.get(arg_name)

                if method in ['delete', 'get']:
                    use_default, arg_value = _get_value(request.G, arg_name, arg_spec, signature)
                else:
                    use_default, arg_value = _get_value(request.P, arg_name, arg_spec, signature, request.B)

                # 未找到参数
                if use_default is None:
                    return mgr.end(HttpResponseBadRequest('Parameter "%s" is required' % arg_name))

                # 使用默认值
                if use_default is True:
                    actual_args.append(arg_value)
                    continue

                # 未指定类型
                if 'annotation' not in arg_spec:
                    actual_args.append(arg_value)
                    continue

                # 检查类型是否一致 #

                # 类型一致，直接使用
                if isinstance(arg_value, arg_spec.annotation):
                    actual_args.append(arg_value)
                    continue

                # 类型不一致，尝试转换类型
                # 转换失败时，会抛出异常
                try:
                    actual_args.append(arg_spec.annotation(arg_value))
                except Exception as e:
                    msg = 'Parameter type of "%s" mismatch, signature: %s' % (arg_name, _get_signature(signature))
                    logger.warning(msg)
                    return mgr.end(HttpResponseBadRequest(msg))

            result = func(*actual_args)

            return mgr.end(_wrap_http_response(mgr, result))

        return caller

    return invoke_route


def _process_json_params(request):
    """
    参数处理
    :return:
    """
    request.B = DotDict()
    request.G = DotDict()
    request.P = DotDict()

    if request.content_type != 'application/json':
        request.G = DotDict.parse(request.GET.dict())
        request.P = DotDict.parse(request.POST.dict())
        return

    # 如果请求是json类型，就先处理一下

    body = request.body

    if body == '' or body is None:
        return

    try:
        if isinstance(body, bytes) or isinstance(body, str):
            request.B = DotDict.parse(json.loads(body))
        elif isinstance(body, dict) or isinstance(body, list):
            request.B = DotDict.parse(body)
    except Exception as e:
        logger.warning('Deserialize request body fail: %s' % str(e))


def _get_signature(signature):
    # 第一个总是  request,去掉
    return '(%s)' % ','.join(str(signature).strip('(').strip(')').split(',')[1:]).strip()


def _parameter_is_missing(signature, arg_name):
    logger.error('Missing required parameter "%s", signature: %s' % (arg_name, _get_signature(signature)))


def _get_value(data: dict, name: str, arg_spec: DotDict, signature, backup: dict = None):
    """

    :param data:
    :param name:
    :param arg_spec:
    :param signature:
    :return: True 表示使用默认值 False 表示未使用默认值 None 表示无值
    """
    # 内容变量时，移除末尾的 _ 符号
    # 内容变量时，移除末尾的 _ 符号
    inner_name = name.rstrip('_')
    if name in data:
        return False, data[name]

    if inner_name in data:
        return False, data[inner_name]

    if backup is not None:
        if name in backup:
            return False, backup[name]

        if inner_name in backup:
            return False, backup[inner_name]

    # 尝试使用默认值
    if 'default' in arg_spec:
        return True, arg_spec.default

    # 缺少无默认值的参数
    _parameter_is_missing(signature, name)
    return None, None


def _wrap_http_response(mgr, data):
    """
    将数据包装成 HttpResponse 返回
    :param data:
    :return:
    """

    # 处理返回函数
    data = mgr.process_return(data)

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
