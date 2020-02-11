# restful-dj

基于 Django2/3 的 restful 自动路由支持。

此包解决的问题：

- 解决 Django 繁锁的路由配置
- 提供更便捷的 restful 编码体验
- 自动解析请求参建，填充到路由目标函数中

## 安装

此包已发布到 PyPI: https://pypi.org/project/restful-dj/ 

```shell script
pip install restful-dj
```

> 此包依赖 Django2/3，但未写入依赖列表中。

## 使用

此包提供的包（package）名称为 `restful_dj`，所有用到的模块都在此包下引入。

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
    'routes': {
        'path.prefix': 'path.to',
    },
    'middleware': [
        'path.to.MiddlewareClass'
    ],
    'logger': 'path.to.logger'
}
```

- **routes** 路由映射配置，即将指定的请求路径映射到指定的代码路径（路径应为基于项目根目录的相对路径）
- **middleware** 中间件配置，其值为一个 `list`，第一个填写一个中间件的完整限定名称
- **logger** 默认的日志是直接打印到控制台的，可以通过设置此值以实现重定向日志输出

### 编写路由

路由文件位置没有要求，只要配置好就可以了。

*test/api/demo.py*

```python
from restful_dj.decorator import route

@route(module='module-name', name='name')
def get(request, param1, param2=None, param3: int =5):
    return {
        'param1': param1, 
        'param2': param2, 
        'param3': param3, 
    }

@route(module='module-name', name='name')
def get_param(request, param1, param2=None, param3: int =5):
    return {
        'param1': param1, 
        'param2': param2, 
        'param3': param3, 
    }
```

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

路由可以返回任何类型的数据。

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
- `**kwargs` *保留参数*

> 这些参数都会被传递给中间件的 `check_login_status` 以及 `check_user_permission` 函数(参数 `meta`)。

同时，此装饰器会自动尝试将 `request.body` 处理成 JSON 格式，并且添加到 `request.JSON` 属性上。

另外，此装饰器会自动将 `request.GET` 和 `request.POST` 处理成为可以通过点号直接访问的对象。例：

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
request.GET.param1
```

### 编写中间件 (可选)

注册到 *settings.py* 的 `RESTFUL_DJ.middleware` 列表中。中间件将按顺序执行。

**需要注意**： 所有的中间件在程序运行期间共享一个实例。

**path.to.MiddlewareClass**

```python
class MiddlewareClass:
    """
    路由中间件
    """

    def __init__(self):
        pass

    def request_process(self, request):
        """
        对 request 对象进行预处理。一般用于请求的数据的解码
        :param request:
        :return: 返回 HttpResponse 以终止请求
        """
        pass

    def response_process(self, request, response):
        """
        对 response 数据进行预处理。一般用于响应的数据的编码
        :param request:
        :param response:
        :return:
        """
        pass

    def check_login_status(self, request, meta):
        """
        检查用户的登录状态，使用时请覆写此方法
        :param request:
        :param meta:
        :return: True|False|HttpResponse 已经登录时返回 True，否则返回 False，HttpResponse 响应
        """
        return True

    def check_user_permission(self, request, meta):
        """
        检查用户是否有权限访问此路由，使用时请覆写此方法
        :param request:
        :param meta:
        :return: True|False|HttpResponse 已经登录时返回 True，否则返回 False，HttpResponse 响应
        """
        return True
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

### 路由收集器 （未完成）

路由收集器用于收集项目中的所有路由，通过以下方式调用:

```python
from restful_dj import collector
routes = collector.collect()
```

在发布产品到线上时，通过此方法将自动产生 Django 的路由配置文件，以提高线上性能。

## 常见问题

### 403 Forbidden. CSRF verification failed. Request aborted. 

移除或注释掉 *settings.py* 文件中的中间件 `'django.middleware.csrf.CsrfViewMiddleware'`
