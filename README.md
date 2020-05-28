# restful-dj

**重要提示：此库当前处于预开发阶段，接口与用法可能发生变化，请勿用于生产环境** 

基于 Django2/3 的 restful 自动路由支持组件。

此包解决的问题：

- 解决 Django 繁锁的路由配置
- 提供更便捷的 restful 编码体验
- 自动解析请求参数，填充到路由处理函数

## 安装

PyPI: https://pypi.org/project/restful-dj/ 

```shell script
pip install restful-dj
```

## 使用

此组件提供的包（package）名称为 `restful_dj`，所有用到的模块都在此包下引入。

### 注册

在项目的根 *urls.py* 文件中，使用以下配置

```python
from django.urls import path
import restful_dj

urlpatterns = [
    path('any/prefix', restful_dj.urls)
]
```

其中，`any/prefix` 是用户自定义的url前缀，可以使用空串 `''`

### 配置

配置项需要写到 *settings.py* 文件中。

```python
RESTFUL_DJ = {
    'global_class': ['path.to.CustomClass',],
    'routes': {
        'path.prefix': 'path.to',
    },
    'middleware': [
        'path.to.MiddlewareClass'
    ],
    'logger': 'path.to.logger'
}
```

- **global_class** 当在路由装饰器参数中使用了自定义的值类型时（比如枚举或类），应该当将其添加到此处，否则无法正确收集到路由
- **routes** 路由映射配置，即将指定的请求路径映射到指定的代码路径（路径应为基于项目根目录的相对路径）
- **middleware** 中间件配置，其值为一个 `list`，第一个填写一个中间件的完整限定名称
- **logger** 默认的日志是直接打印到控制台的，可以通过设置此值以实现重定向日志输出

*test.py*
```python
from restful_dj import route
from enums import RouteTypes
@route('module_name', 'route_name', route_type = RouteTypes.TEST)
def test(req):
    pass
```

*enums.py*
```python
from enum import Enum
class RouteTypes(Enum):
    TEST = 1
```

### 编写路由

路由文件位置没有要求，只要配置好就可以了。

*test/api/demo.py*

```python
from django.http import HttpRequest
from restful_dj.decorator import route

@route(module='module-name', name='name')
def get(request, param1, param2=None, param3: int =5):
    # request 会是 HttpRequest
    return {
        'param1': param1, 
        'param2': param2, 
        'param3': param3, 
    }

@route(module='module-name', name='name')
def get_param(param1, req: HttpRequest, from_=None, param3 =5):
    # req 会是 HttpRequest
    return {
        'param1': param1, 
        'from': from_, 
        'param3': param3,
    } 

@route(module='module-name', name='name')
def get_param(request: str, param1, from_=None, param3 =5):
    # request 会是请求参数，参数列表中没有 HttpRequest
    return {
        'request': request,
        'param1': param1, 
        'from': from_, 
        'param3': param3,
    } 

@route(module='module-name', name='name')
def get_param(request, param1, from_=None, param3 =5, **kwargs):
    # 未在函数的参数列表中声明的请求参数，会出现在 kwargs 中
    return {
        'param1': param1,
        'from': from_,
        'param3': param3,
        'variable_args': kwargs
    }

```

一些需要注意的地方：

- 当代码中需要使用关键字作为名称时，请在名称后添加 `_`，此时前端请求时，`_` 符号可省略，
如: `from_` 在请求时可写作 `from=test` （`from_=test` 亦可）。
- 对于语言间的命令差异，可以自动兼容 `下划线命名法` 与 `驼峰命名法`，如：请求参数中的 `pageIndex`，在处理函数中可以写作 `page_index`或`_page_index_` ，
也就是说，在前后添加 `_` 符号都不会影响参数的解析。
- 路由处理函数可以添加一个可变参数(如：`**kwargs**`)，用于接收未在参数列表中列出的请求项。
当然，`kwargs`和普通函数一样，可以是任何其它名称。
- `request` 参数(与参数位置无关)，可能被解析成三种结果(`1`和`2`均会将其作为 `HttpRequest` 参数处理)：
    1. 参数名称为 `request`，并且未指定参数类型(或指定类型为 `HttpRequest`)
    2. 参数类型为 `HttpRequest`，参数名称可以是任何合法的标识符
    3. 参数名称为 `request`，声明了不是 `HttpRequest` 的类型，此时会被解析成一般的请求参数
    
    

再写配置

```python
RESTFUL_DJ = {
    'routes': {
        'test': 'test.api',
    }
}
```

此配置表示，所有请求中以 `test` 开头的地址，都会交由 `test.api` 下的模块进行处理。

前端调用:

```javascript
// 请求 get 函数
ajax.get('test.demo?param1=1&param2=2&param3=3')

// 请求 get_param 函数
ajax.get('test.demo/param?param1=1&param2=2&param3=3')
```

路由可以返回任何类型的数据。路由会自动根据函数定义来判断传入参数的类型是否合法。

比如前面示例中的 `param3: int =5`，会根据声明类型 `int` 去判断传入类型
- 如果传入了字符串类型的数值，路由会自动转换成数值类型
- 另外，如果设置了 `None` 以外的默认值，那么路由会根据默认值的类型自动去判断，
此时可以省略参数类型，如: `param3: int =5` 省略为 `param3=5`

### 装饰器 `route`

装饰器 `route` 用于声明某个函数可以被路由使用。通过添加此装饰器以限制非路由函数被非法访问。

声明为：

```python
def route(module=None, name=None, permission=True, ajax=True, referer=None, **kwargs):
    pass
```

- `module` 此路由所属的业务/功能模块名称
- `name` 此路由的名称
- `permission` 设置此路由是否有权限控制
- `ajax` 设置此路由是否仅允许 **ajax** 访问 *保留参数*
- `referer` 设置此路由允许的 **referer** 地址 *保留参数*
- `**kwargs` *额外参数*

> 这些参数都会被传递给中间件的各个函数的参数 `meta`。详细见 [RouteMeta](#RouteMeta)

同时，此装饰器会自动尝试将 `request.body` 处理成 JSON 格式(仅在 `content-type=application/json` 时)，并且添加到 `request.B` 属性上。

另外，此装饰器会自动将 `request.GET` 和 `request.POST` 处理成为可以通过点号直接访问的对象，分别添加到 `request.G` 和 `request.P` 上。例：

```python
# 原始数据
request = {...}
request.GET = {
    'param1': 1,
    'param2': 2
}
# 此时，只能这样访问
request.GET['param1']

# 而在经过装饰器的处理后，可以这样访问
request.G.param1
```

但是，一般情况下，使用路由处理函数就能完全操作请求参数的，
所以需要在代码中尽量减少使用 `B/P/G`，以避免代码的不明确性。

### 分发前的处理 (可选)

有的时候，需要在分发前对请求参数进行处理。此时可以使用 `restful.set_before_dispatch_handler` 来进行一些预处理。

函数签名:

```python
def set_before_dispatch_handler(handler):
    pass
```

用法:

```python
import restful_dj

def before_dispatch_handler(request, entry, name):
    # 可以在此处修改 request 的数据
    # 也可以重新定义 entry 和 name
    return entry, name

restful_dj.set_before_dispatch_handler(before_dispatch_handler)
```

### 编写中间件 (可选)

#### RouteMeta

路由元数据。

```python
from types import FunctionType
from typing import OrderedDict

class RouteMeta:  
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
```

注册到 *settings.py* 的 `RESTFUL_DJ.middleware` 列表中。中间件将按顺序执行。

**需要注意**： 每一个中间件在程序运行期间共享一个实例。

**path.to.MiddlewareClass**

```python
from django.http import HttpRequest
from restful_dj import RouteMeta 

class MiddlewareClass:
    """
    路由中间件
    """

    def process_request(self, request: HttpRequest, meta: RouteMeta, **kwargs):
        """
        对 request 对象进行预处理。一般用于请求的数据的解码，此时路由组件尚水进行请求数据的解析(B,P,G 尚不可用)
        :param request:
        :param meta:
        :return: 返回 HttpResponse 以终止请求，返回 False 以停止执行后续的中间件(表示访问未授权)，返回 None 或不返回任何值继续执行后续中间件
        """
        pass

    def process_invoke(self, request: HttpRequest, meta: RouteMeta, **kwargs):
        """
        在路由函数调用前，对其参数等进行处理，此时路由组件已经完成了请求数据的解析(B,P,G 已可用)
        此时可以对解析后的参数进行变更
        :param request:
        :param meta:
        :return: 返回 HttpResponse 以终止请求，返回 False 以停止执行后续的中间件(表示访问未授权)，返回 None 或不返回任何值继续执行后续中间件
        """
        pass

    def process_return(self, request: HttpRequest, meta: RouteMeta, **kwargs):
        """
        在路由函数调用后，对其返回值进行处理
        :param request:
        :param meta:
        :param kwargs: 始终会有一个 'data' 的项，表示返回的原始数据
        :return: 返回 HttpResponse 以终止执行，否则返回新的 return value
        """
        assert 'data' in kwargs
        return kwargs['data']

    def process_response(self, request: HttpRequest, meta: RouteMeta, **kwargs):
        """
        对 response 数据进行预处理。一般用于响应的数据的编码
        :rtype: HttpResponse
        :param meta:
        :param request:
        :param kwargs: 始终会有一个 'response' 的项，表示返回的 HttpResponse
        :return: 无论何种情况，应该始终返回一个  HttpResponse
        """
        assert 'response' in kwargs
        return kwargs['response']
```

### 设置日志记录器 (可选)

```python
from restful_dj import set_logger

def my_logger(level: str, message: str, e: Exception):
    pass

set_logger(my_logger)
```

其中，`level`表示日志级别，会有以下值：

- debug
- info
- success
- warning
- error

### 路由收集

路由收集器用于收集项目中的所有路由，通过以下方式调用:

```python
from restful_dj import collector
routes = collector.collect()
```

> `routes` 是一个可以直接迭代的路由数组

在发布产品到线上时，通过此方法将自动产生 Django 的路由配置文件，以提高线上性能。

## 待办事项

无

## 常见问题

### 403 Forbidden. CSRF verification failed. Request aborted. 

移除或注释掉 *settings.py* 文件中的中间件 `'django.middleware.csrf.CsrfViewMiddleware'`

## 更新记录

> 开发阶段暂不记录