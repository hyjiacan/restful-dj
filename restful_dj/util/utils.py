import inspect
from collections import OrderedDict


class ArgumentSpecification:
    """
    函数参数声明
    """

    def __init__(self, index: int):
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
        spec = ArgumentSpecification(index)
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
    return __import__(module_name, fromlist=True)
