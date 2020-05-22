import re


class DotDict(dict):
    """
    定义一个允许通过点号访问的dict
    """

    def __init__(self, *args, **kwargs):
        """
        初始化
        :param args:
        :param kwargs:
        """
        dict.__init__(self, *args, **kwargs)
        self.__dict__ = self

    def __str__(self):
        return dict.__str__(self)

    def __repr__(self):
        return dict.__repr__(self)

    @staticmethod
    def parse(obj, handle_key=True):
        """
        把 dict 转换成可以通过 . 号访问的 DotDict
        :param obj: dict,list
        :param handle_key: 是否处理特殊 key
        :return:
        """

        if not isinstance(obj, (dict, list)):
            return obj

        dot_dict = DotDict()

        # 处理 dict
        if isinstance(obj, dict):
            for (key, value) in obj.items():
                if handle_key:
                    # 处理特殊的key
                    zh_pattern = re.compile(u'[\u4e00-\u9fa5]+')
                    match = zh_pattern.search(key)
                    if not match:
                        key = re.sub(r'[^0-9a-zA-Z_]', '_', key)
                        # 如果第一个字符不是标识符 就在前面添加一个下划线
                        if not re.match(r'^[a-zA-Z_]', key):
                            key = '_' + key
                setattr(dot_dict, key, DotDict.__parse_value(value, handle_key))
            return dot_dict

        # 处理list
        return list(map(lambda item: DotDict.parse(item), obj))

    @staticmethod
    def __parse_value(value, handle_key=True):
        # 处理列表类型
        if isinstance(value, list):
            return list(map(lambda item: DotDict.__parse_value(item, handle_key), value))

        # 处理字典类型
        if isinstance(value, dict):
            return DotDict.parse(value, handle_key)

        # 普通类型
        return value
