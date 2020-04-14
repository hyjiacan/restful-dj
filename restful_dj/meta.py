class RouteMeta:
    """
    路由元数据
    """

    def __init__(self, handler, id=None, module=None, name=None, permission=True, ajax=True, referer=None, kwargs=None):
        self._handler = handler
        self._id = id
        self._module = module
        self._name = name
        self._permission = permission
        self._ajax = ajax
        self._referer = referer
        self._kwargs = {} if kwargs is None else kwargs

    @property
    def handler(self):
        return self.handler

    @property
    def id(self):
        return self._id

    @property
    def module(self):
        return self._module

    @property
    def name(self):
        return self._name

    @property
    def permission(self):
        return self._permission

    @property
    def ajax(self):
        return self._ajax

    @property
    def referer(self):
        return self._referer

    @property
    def kwargs(self):
        return self._kwargs
