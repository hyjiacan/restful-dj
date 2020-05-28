from types import FunctionType
from typing import OrderedDict


class RouteMeta:
    """
    路由元数据
    """

    def __init__(self,
                 handler: FunctionType,
                 func_args,
                 route_id=None,
                 module=None,
                 name=None,
                 permission=True,
                 ajax=True,
                 referer=None,
                 kwargs=None):
        """

        :param handler: 路由处理函数对象
        :param func_args: 路由处理函数参数列表
        :param route_id: 路由ID，此ID由路由相关信息组合而成
        :param module: 装饰器上指定的 module 值
        :param name: 装饰器上指定的 name 值
        :param permission: 装饰器上指定的 name 值
        :param ajax: 装饰器上指定的 name 值
        :param referer: 装饰器上指定的 name 值
        :param kwargs: 装饰器上指定的其它参数
        """
        self._handler = handler
        self._func_args = func_args
        self._id = route_id
        self._module = module
        self._name = name
        self._permission = permission
        self._ajax = ajax
        self._referer = referer
        self._kwargs = {} if kwargs is None else kwargs

    @property
    def handler(self) -> FunctionType:
        """
        路由处理函数对象
        :return:
        """
        return self._handler

    @property
    def func_args(self) -> OrderedDict:
        """
        路由处理函数参数列表
        :return:
        """
        return self._func_args

    @property
    def id(self) -> str:
        """
        路由ID，此ID由路由相关信息组合而成
        :return:
        """
        return self._id

    @property
    def module(self) -> str:
        """
        装饰器上指定的 module 值
        :return:
        """
        return self._module

    @property
    def name(self) -> str:
        """
        装饰器上指定的 name 值
        :return:
        """
        return self._name

    @property
    def permission(self) -> bool:
        """
        装饰器上指定的 permission 值
        :return:
        """
        return self._permission

    @property
    def ajax(self) -> bool:
        """
        装饰器上指定的 ajax 值
        :return:
        """
        return self._ajax

    @property
    def referer(self) -> str:
        """
        装饰器上指定的 referer 值
        :return:
        """
        return self._referer

    @property
    def kwargs(self) -> dict:
        """
        装饰器上指定的其它参数
        :return:
        :rtype: Dict
        """
        return self._kwargs
