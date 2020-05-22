import inspect
import re
from collections import OrderedDict
from re import Match

from django.http import HttpRequest


def _get_parameter_alias(match: Match):
    ch = match.group('ch')
    return '' if ch is None else ch.upper()


class ArgumentSpecification:
    """
    函数参数声明
    """

    def __init__(self, name: str, index: int):
        """

        :param name: 参数名称
        :param index: 参数在参数位置中的位置
        """
        self.name = name
        self.index = index
        # 是否是可变参数
        self.is_variable = False
        # 是否有类型声明
        self.has_annotation = False
        # 是否有默认值
        self.has_default = False
        # 类型声明
        self.annotation = None
        # 默认值
        self.default = None
        # 别名，当路由处理函数中声明的是 abc_def 时，自动处理为 abcDef
        # 同时会移除所有的 _ 符号
        self.alias = re.sub('_+(?P<ch>.?)', _get_parameter_alias, name)
        # 如果与原名称相同，那么就设置为 None 表示无别名
        if self.alias == name:
            self.alias = None

    def __str__(self):
        arg_type = self.annotation.__name__ if self.has_annotation else 'any'

        if self.alias is None:
            return '%s: %s' % (self.name, arg_type)

        return '%s/%s: %s' % (self.name, self.alias, arg_type)


def get_func_args(func):
    """
    获取函数的参数列表（带参数类型）
    :param func:
    :return:
    """
    signature = inspect.signature(func)
    parameters = signature.parameters
    _empty = signature.empty

    args = OrderedDict()
    index = 0
    for p in parameters.keys():
        parameter = parameters.get(p)
        spec = ArgumentSpecification(p, index)
        spec.is_variable = parameter.kind == parameter.VAR_KEYWORD

        index += 1
        # 类型
        annotation = parameter.annotation
        default = parameter.default

        if default != _empty:
            spec.default = default
            spec.has_default = True

        # 有默认值时，若未指定类型，则使用默认值的类型
        if annotation == _empty:
            if default is not None and default != _empty:
                spec.annotation = type(default)
                spec.has_annotation = True
            elif p == 'request':
                # 以下情况将设置为 HttpRequest 对象
                # 1. 当参数名称是 request 并且未指定类型
                # 2. 当参数类型是 HttpRequest 时 (不论参数名称，包括 request)
                # 但是，参数名称是 request 但其类型不是 HttpRequest ，就会被当作一般参数处理
                spec.annotation = HttpRequest
                spec.has_annotation = True
        else:
            spec.annotation = annotation
            spec.has_annotation = True

        args[p] = spec

    return args


def load_module(module_name: str):
    """
    加载模块
    :param module_name:
    :return:
    """
    # noinspection PyTypeChecker
    return __import__(module_name, fromlist=True)
