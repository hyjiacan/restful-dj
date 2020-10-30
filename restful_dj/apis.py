import os

from django import shortcuts
from django.conf import settings
from django.http import HttpResponseNotFound, JsonResponse

from restful_dj.router import Router
from restful_dj.util import collector
from restful_dj.util.utils import ArgumentSpecification

# 开发模式的模块缓存，用于API列表
MODULES_CACHE = None


def register_template_dir():
    template_conf = settings.TEMPLATES[0]
    if 'DIRS' not in template_conf:
        template_conf['DIRS'] = []

    template_conf['DIRS'].append(os.path.join(os.path.dirname(__file__), 'templates'))


def render(request):
    if not settings.DEBUG:
        return HttpResponseNotFound()

    if request.method != 'POST':
        return shortcuts.render(request, 'restful_dj_api_list_template.html')

    global MODULES_CACHE

    if MODULES_CACHE is None:
        routes = collector.collect()

        modules = {}

        for route in routes:
            module = route['module']

            p = route['path']
            suffix = ''
            temp = p.split('/')
            entry = temp[0]
            if len(temp) == 2:
                suffix = temp[1]

            router = Router(request, route['method'], entry, suffix)
            router.check()
            define = router.get_func_define()
            if define and len(define['args']) > 0:
                route['args'] = [define['args'][arg] for arg in define['args']]
            else:
                route['args'] = None

            # 不需要 kwargs ，因为其中的数据是无法预估的，在api列表中也没有多大的意义
            if 'kwargs' in route:
                del route['kwargs']

            if module in modules:
                modules[module].append(route)
            else:
                modules[module] = [route]
        MODULES_CACHE = modules

    return JsonResponse(MODULES_CACHE, encoder=ArgumentSpecification.JsonEncoder)
