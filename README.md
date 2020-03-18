# restful-dj

基于 Django2/3 的 restful 自动路由支持。

此包解决的问题：

- 解决 Django 繁锁的路由配置
- 提供更便捷的 restful 编码体验
- 自动解析请求参数，填充到路由目标函数中

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
def get_param(request, param1, from_=None, param3 =5):
    return {
        'param1': param1, 
        'from': from_, 
        'param3': param3, 
    }
```

> 当代码中需要使用关键字作为名称时，请在名称后添加 `_`，此时前端请求时，`_` 符号可省略，如:
> `from_` 在请求时可写作 `from=test` （`from_=test` 亦可）。 since 0.1.3

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

> since 0.1.3:
> 路由会自动根据函数定义来判断传入参数的类型是否合法。
> 比如前面示例中的 `param3: int =5`，会根据声明类型 `int` 去判断传入类型，
> 如果传入了字符串类型的数值，路由会自动转换成数值类型。
> 另外，如果设置了 `None` 以外的默认值，那么路由会根据默认值的类型自动去判断，
> 此时可以省略参数类型，如: `param3: int =5` 省略为 `param3=5`

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

同时，此装饰器会自动尝试将 `request.body` 处理成 JSON 格式，并且添加到 `request.B` 属性上。

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

### 分发前的处理 (可选)

> Since *0.1.2*

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

### 路由收集

路由收集器用于收集项目中的所有路由，通过以下方式调用:

```python
from restful_dj import collector
routes = collector.collect()
```

> `routes` 是一个可以直接迭代的路由数组

在发布产品到线上时，通过此方法将自动产生 Django 的路由配置文件，以提高线上性能。

## 待办事项

> 暂无

## 常见问题

### 403 Forbidden. CSRF verification failed. Request aborted. 

移除或注释掉 *settings.py* 文件中的中间件 `'django.middleware.csrf.CsrfViewMiddleware'`

## 更新记录

### 0.2.0

- 优化 请求参数解析

### 0.1.5

- 修复 路由装饰器逻辑错误
- 修复 路由中间件的 `response_process` 函数未被调用的问题

### 0.1.4

- 修复 中间件导致请求无法响应的问题
- 添加 路由调用前的参数检查支持
- 修复 GET/POST 参数为数组时只能获取到第一个值的问题

### 0.1.3

- 优化 日志输出
- 参数名称以 `_` 结束时，表示此名称可能是关键字，此时需要匹配无此后缀的变量名，如： `from_` 应该匹配为  `from`
- 检查传入的参数类型与声明是否一致（如果有声明）
- 参数错误时，在**调试模式**下显示更友好的提示: 展示原函数参数定义
- 完成 路由收集接口
- 优化 线上模式时，使用路由缓存

### 0.1.2

- 添加 路由请求分发前的处理支持 `restful_dj.set_before_dispatch_handler`

### 0.1.1

- 修复 路由分发错误 