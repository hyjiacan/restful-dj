# coding: utf-8

# 此模块用于收集路由

import os
import re
from os import path

from django.conf import settings


def _get_env(*args):
    from .setting import GLOBAL_CLASSES
    env = {}

    # 加载全局配置
    for arg in GLOBAL_CLASSES:
        env[arg.__name__] = arg

    # 加载接口参数
    # 若存在相同的名称，则会被覆盖
    for arg in args:
        env[arg.__name__] = arg
    return env


def _get_route_map():
    from restful_dj.util.setting import APP_CONFIG_ROUTE, CONFIG_ROOT
    if APP_CONFIG_ROUTE not in CONFIG_ROOT:
        raise Exception('restful-dj: route map setting not found')

    routes = CONFIG_ROOT[APP_CONFIG_ROUTE]

    if len(routes) == 0:
        raise Exception('restful-dj: route map setting is empty')

    return routes.items()


def collect(*environments):
    """
    执行收集操作
    :return: 所有路由的集合
    """
    # 为 route 提供的执行环境
    # 读取在 settings.py 中配置的环境
    route_env = _get_env(fake_route, *environments)
    project_root = settings.BASE_DIR

    # 所有路由的集合
    routes = []

    for (http_prefix, pkg_prefix) in _get_route_map():
        route_root = path.abspath(path.join(project_root, pkg_prefix.replace('.', path.sep)))

        # 遍历目录，找出所有的 .py 文件
        for (dir_name, dirs, files) in os.walk(route_root):
            # 可能是包
            pkg_file = path.abspath(path.join(dir_name, '__init__.py'))
            if path.exists(pkg_file) and path.isfile(pkg_file):
                get_route_defines(route_root, pkg_file, http_prefix, pkg_prefix, routes, route_env)

            for file in files:
                # 不是 .py 文件，忽略
                if not file.endswith('.py'):
                    continue

                fullname = path.abspath(path.join(dir_name, file))
                # 解析文件
                get_route_defines(route_root, fullname, http_prefix, pkg_prefix, routes, route_env)

            for sub_dir_name in dirs:
                pkg_file = path.abspath(path.join(sub_dir_name, '__init__.py'))
                if path.exists(pkg_file) and path.isfile(pkg_file):
                    get_route_defines(route_root, pkg_file, http_prefix, pkg_prefix, routes, route_env)

    return routes


def get_route_defines(route_root, fullname, http_prefix, pkg_prefix, routes, route_env):
    for define in resolve_file(route_root, fullname, http_prefix, pkg_prefix, route_env):
        # 返回 None 表示没有找到定义
        if define is None:
            continue
        routes.append(define)


def resolve_file(route_define, fullname, http_prefix, pkg_prefix, route_env: dict):
    """
    解析文件
    :param route_env:
    :param pkg_prefix:
    :param http_prefix: http 请求前缀
    :param route_define: 路由文件的根路径
    :param fullname: 文件的完整路径
    :return: 没有路由时返回 None
    """
    with open(fullname, encoding='utf-8') as python_fp:
        lines = python_fp.readlines()
        python_fp.close()
    source = ''.join(lines)

    # 解析路由的定义
    # defines = re.compile(r'^@(route\(.+?\)).*(\n.*?)+^def (.+?)\(', re.M).findall(source)
    defines = re.compile(r'^@(route\(.+?\))(.*?)^def (.+?)\(', re.M | re.S).findall(source)
    # 没有找到定义，返回 None
    if len(defines) == 0:
        yield None

    # router_str 是在函数上声明的装饰器定义
    # other_lines 是装饰器与函数声明间的其它代码
    # func 是函数的名称
    for (router_str, other_lines, func) in defines:
        # 解析出请求的方法(method)与请求的指定函数名称
        method, name = resolve_func(func)
        # 利用 eval 解析出路由的定义（在这个文件中定义了与装饰器相同的函数，以便于读取装饰器的参数）
        router_str = router_str.replace('route', 'fake_route')
        define = eval(router_str, route_env)
        # 构造http请求的地址
        # -3 是为了干掉最后的 .py 字样
        pkg = re.sub(r'[/\\]', '.', path.relpath(fullname, route_define))[0:-3]

        # 当是包时，移除 __init__ 部分
        if pkg.endswith('.__init__'):
            http_path = '%s.%s' % (http_prefix, pkg[0:-len('.__init__')])
        else:
            http_path = '%s.%s' % (http_prefix, pkg)
        # 如果指定了名称，就追加到地址后
        if name is not None:
            http_path += '/' + name

        pkg = '%s.%s' % (pkg_prefix, pkg)
        # 唯一标识
        define['id'] = '%s_%s' % (pkg.replace('_', '__').replace('.', '_'), func)
        # 路由所在包名称
        define['pkg'] = pkg
        # 路由所在文件的完整路径
        define['file'] = fullname
        # 路由请求的处理函数
        define['handler'] = func
        # 路由的请求方法
        define['method'] = method
        # 路由的请求路径
        define['path'] = http_path

        yield define


def fake_route(module=None, name=None, login=True, permission=True, ajax=True, referer=None, **kwargs):
    """
    此函数用于帮助读取装饰器的参数
    :param module:
    :param name:
    :param login:
    :param permission:
    :param ajax:
    :param referer:
    :param kwargs:
    :return:
    """

    return {
        'module': module,
        'name': name,
        'login': login,
        'permission': permission,
        'ajax': ajax,
        'referer': referer,
        'kwargs': kwargs
    }


def resolve_func(func: str):
    """
    从处理函数中解析出路由的 method 与指定名称
    :param func:
    :return:
    """
    method, lodash, name = re.match(r'(get|post|delete|put|option|patch|connect)(_(.+))?', func).groups()
    return method, name
