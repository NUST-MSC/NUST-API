# coding: utf-8
"""Miscellaneous utility functions and classes.
"""

from tornado.util import Configurable

if type('') is not type(b''):
    def u(s):
        return s
    bytes_type = bytes
    unicode_type = str
    basestring_type = str
else:
    def u(s):
        return s.decode('unicode_escape')
    bytes_type = str
    unicode_type = unicode
    basestring_type = basestring


class Cache(Configurable):
    """ 缓存部分数据的缓存. 例如用来维护登录的 Session, 避免一次登录请求
    可以实现使用内存的缓存(MemCache), 基于Redis的缓存(TODO)
    """

    @classmethod
    def configurable_base(cls):
        return Cache

    @classmethod
    def configurable_default(cls):
        return MemCache

    def initialize(self):
        pass

    def get(self, key):
        """ 依据 key 获取内容
        """
        raise NotImplementedError()

    def set(self, key, value):
        """ 设置 key 对应值为value
        """
        raise NotImplementedError()

    def remove(self, key):
        """ 使 key 失效
        """
        raise NotImplementedError()


class MemCache(Cache):
    def __init__(self):
        self._dict = dict()

    def get(self, key):
        return self._dict.get(key, None)

    def set(self, key, value):
        self._dict[key] = value
        return self

    def remove(self, key):
        del self._dict[key]
