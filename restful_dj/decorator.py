import json
from collections import OrderedDict
from functools import wraps

from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpRequest

from .meta import RouteMeta
from .middleware import MiddlewareManager
from .util.dot_dict import DotDict

from .util import logger
from .util.utils import ArgumentSpecification


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

            mgr = MiddlewareManager(
                request,
                RouteMeta(
                    func_name,
                    id='{0}_{1}'.format(func.__module__.replace('_', '__').replace('.', '_'), func_name),
                    module=module,
                    name=name,
                    permission=permission,
                    ajax=ajax,
                    referer=referer,
                    kwargs=kwargs,
                )
            )

            # 处理请求中的json参数
            # 处理后可能会在 request 上添加一个 json 的项，此项存放着json格式的 body 内容
            _process_json_params(request)

            # 调用中间件，以处理请求
            result = mgr.begin()

            # 返回了 HttpResponse，直接返回此对象
            if isinstance(result, HttpResponse):
                return mgr.end(result)

            # 返回了 False，表示未授权访问
            if result is False:
                return mgr.end(HttpResponseUnauthorized())

            # 返回了 HttpResponse ， 直接返回此对象
            if isinstance(result, HttpResponse):
                return mgr.end(result)

            # 调用路由处理函数
            arg_len = len(args)
            if arg_len == 0:
                return mgr.end(_wrap_http_response(mgr, func()))

            # 有参数，自动从 queryString, POST 或 json 中获取
            # 匹配参数

            actual_args = _get_actual_args(request, func, args)

            if isinstance(actual_args, HttpResponse):
                return mgr.end(actual_args)

            result = func(**actual_args)

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
        if isinstance(body, (bytes, str)):
            request.B = DotDict.parse(json.loads(body))
        elif isinstance(body, (dict, list)):
            request.B = DotDict.parse(body)
    except Exception as e:
        logger.warning('Deserialize request body fail: %s' % str(e))


def _parameter_is_missing(signature, arg_name):
    logger.error('Missing required parameter "%s", signature: %s' % (arg_name, str(signature)))


def _get_value(data: dict, name: str, arg_spec: ArgumentSpecification, signature, backup: dict = None):
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

    # 使用默认值
    if arg_spec.has_default:
        return True, arg_spec.default

    # 缺少无默认值的参数
    _parameter_is_missing(signature, name)
    return None, None


def _get_actual_args(request: HttpRequest, func, args: OrderedDict) -> dict or HttpResponse:
    method = request.method.lower()
    actual_args = {}

    import inspect
    signature = inspect.signature(func)

    # 已使用的参数名称，用于后期填充可变参数时作排除用
    used_args = []
    # 是否声明了可变参数
    has_variable_args = False

    arg_source = request.G if method in ['delete', 'get'] else request.P

    for arg_name in args.keys():
        arg_spec = args.get(arg_name)

        # 如果是可变参数：如: **kwargs
        # 设置标记，以在后面进行填充
        if arg_spec.is_variable:
            has_variable_args = True
            continue

        # 以及情况将传入 HttpRequest 对象
        # 1. 当参数名称是 request 并且未指定类型
        # 2. 当参数类型是 HttpRequest 时 (不论参数名称，包括 request)
        # 但是，参数名称是 request 但其类型不是 HttpRequest ，就会被当作一般参数处理
        if arg_name == 'request' and not arg_spec.has_annotation:
            actual_args[arg_name] = request
            continue
        if arg_spec.annotation == HttpRequest:
            actual_args[arg_name] = request
            continue

        use_default, arg_value = _get_value(arg_source, arg_name, arg_spec, signature, request.B)

        # 未找到参数
        if use_default is None:
            return HttpResponseBadRequest('Parameter "%s" is required' % arg_name)

        # 使用默认值
        if use_default is True:
            actual_args[arg_name] = arg_value
            used_args.append(arg_name)
            continue

        # 未指定类型
        if not arg_spec.has_annotation:
            actual_args[arg_name] = arg_value
            used_args.append(arg_name)
            continue

        # 检查类型是否一致 #

        # 类型一致，直接使用
        if isinstance(arg_value, arg_spec.annotation):
            actual_args[arg_name] = arg_value
            used_args.append(arg_name)
            continue

        # 类型不一致，尝试转换类型
        # 转换失败时，会抛出异常
        try:
            # 当 arg_value 是字符串，arg_spec的类型是对象时，尝试解析成 json
            if arg_spec.annotation in (dict, list) and isinstance(arg_value, str):
                try:
                    arg_value = json.loads(arg_value)
                    if isinstance(arg_value, (list, dict)):
                        arg_value = DotDict.parse(arg_value)
                except:
                    # 此处的异常直接忽略即可
                    logger.warning('Value for "%s!%s" may be incorrect: %s' % (func.__name__, arg_name, arg_value))

                # 类型一致，直接使用
                if isinstance(arg_value, arg_spec.annotation):
                    actual_args[arg_name] = arg_value
                    used_args.append(arg_name)
                    continue
            actual_args[arg_name] = arg_spec.annotation(arg_value)
            used_args.append(arg_name)
        except:
            msg = 'Parameter type of "%s" mismatch, signature: %s' % (arg_name, str(signature))
            logger.warning(msg)
            return HttpResponseBadRequest(msg)

    if not has_variable_args:
        return actual_args

    # 填充可变参数
    variable_args = {}
    for item in arg_source:
        if item in used_args:
            continue
        variable_args[item] = arg_source[item]

    for item in request.B:
        if item in used_args:
            continue
        variable_args[item] = request.B[item]

    actual_args.update(variable_args)

    return actual_args


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
