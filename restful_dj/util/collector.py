# coding: utf-8

# 此模块用于收集路由，并自动生成配置文件

import os
import re
import time
from os import path


def collect(app_root: str):
    """
    执行收集操作
    :param app_root:
    :return: 所有路由的集合
    """
    # 存放路由文件的根目录
    router_root = path.abspath(path.join(app_root, 'api/entry'))

    # 所有路由的集合
    routers = []

    # 遍历目录，找出所有的 .py 文件
    for (dirname, dirs, files) in os.walk(path.join(app_root, 'api/entry')):
        for file in files:
            # 不是 .py 文件，忽略
            if not file.endswith('.py'):
                continue

            fullname = path.abspath(path.join(dirname, file))
            # 解析文件
            for define in resolve_file(router_root, fullname):
                # 返回 None 表示没有找到定义
                if define is None:
                    continue
                routers.append(define)
    return routers


def resolve_file(router_define, fullname):
    """
    解析文件
    :param router_define: 路由文件的根路径
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
    for (route_str, other_lines, func) in defines:
        # 解析出请求的方法(method)与请求的指定函数名称
        method, name = resolve_func(func)
        # 利用 eval 解析出路由的定义（在这个文件中定义了与装饰器相同的函数，以便于读取装饰器的参数）
        route_str = route_str.replace('route', 'fake_route')
        define = eval(route_str, globals())
        # 构造http请求的地址
        # -3 是为了干掉最后的 .py 字样
        pkg = re.sub(r'[/\\]', '.', path.relpath(fullname, router_define))[0:-3]
        http_path = '/api/' + pkg
        # 如果指定了名称，就追加到地址后
        if name is not None:
            http_path += '/' + name

        # 完整的包路径
        pkg = 'api.entry.{0}'.format(pkg)
        # 唯一标识
        define['id'] = '{0}_{1}'.format(pkg.replace('_', '__').replace('.', '_'), func)
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


def build_file(routers):
    """
    生成路由
    :return:
    """
    print("Begin build routers, {0} routers found in total".format(len(routers)))
    imports = []
    handlers = []

    for router in routers:
        print(router['path'])
        imports.append("from {0} import {1} as {2}".format(router['pkg'], router['handler'], router['id']))
        # 移除前缀 /api/ 字符
        handlers.append("path('{0}', {1})".format(router['path'][5:], router['id']))

        route_file = path.join(root, 'api/routers.py')
        # 删除已经存在的文件
        if path.exists(route_file):
            os.unlink(route_file)
        with open(route_file, encoding='utf-8', mode='w+') as router_fp:
            router_fp.write('''# coding: utf-8

    # ========================================================== #
    # THIS FILE IS GENERATED AUTOMATICALLY, DO NOT EDIT MANUALLY # 
    # 此文件由程序在初始化时自动生成, 请不要手动编辑                # 
    # ========================================================== #

    GENERATED_TIME = '%s'

    from django.urls import path
    ''' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))
            for import_stmt in imports:
                router_fp.write("{0}\n".format(import_stmt))

            router_fp.write('''
    ROUTE_MAP = [
    ''')

            for handler in handlers:
                router_fp.write("    {0},\n".format(handler))

            router_fp.write(''']
    ''')
            router_fp.close()

    print('Routers are generated')


if __name__ == '__main__':
    # root = path.abspath('E:\\work\\project\\src\\ywcz_vue\\luffy')
    root = '../..'
    _routers = collect(root)
    print(_routers)
    # build_file(_routers)
