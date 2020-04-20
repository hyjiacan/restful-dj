import inspect
from collections import OrderedDict

from .dot_dict import DotDict


def get_func_args(func):
    """
    获取函数的参数列表（带参数类型）
    :param func:
    :return:
    """
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

    return args


def load_module(module_name: str):
    """
    加载模块
    :param module_name:
    :return:
    """
    return __import__(module_name, fromlist=True)
