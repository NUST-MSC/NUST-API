# coding: utf-8

from __future__ import absolute_import

from urllib.parse import urlencode
from hashlib import md5
import json
import re
import datetime
import os

from tornado import gen
from tornado.httpclient import AsyncHTTPClient as HTTPClient
from tornado.httpclient import HTTPRequest
import bs4.element
import requests

from util import Cache, unicode_type, bytes_type

cache = Cache()
jwc_domain = 'http://202.119.81.112:9080'


def login_data(username, password):
    if isinstance(password, unicode_type):
        password = password.encode('utf-8')
    data = {
        'method': 'verify',
        'USERNAME': username,
        'PASSWORD': md5(password).hexdigest().upper()
    }
    return data


def login_session(username, password):
    data = login_data(username, password)
    http = requests.Session()
    res = http.get(jwc_domain + '/njlgdx/xk/LoginToXk', params=data)
    if re.search(u'退出', res.text):
        return http


def get_class_sys_data():
    data = cache.get('class_sys_data')
    if data:
        return data
    else:
        with open('./jwc/class_type.json') as f:
            cache.set('class_sys_data', json.load(f))
        return cache.get('class_sys_data')


def get_current_term():
    def fetch_curent_term():
        """ 请求查询当前学期, 跑去考试安排查询看看默认的学期即可
        """
        user = os.getenv("TEST_JWC_USER") or input("测试教务处帐号:")
        pwd = os.getenv("TEST_JWC_PWD") or input("测试教务处密码:")
        http = login_session(user, pwd)
        r = http.get(jwc_domain + '/njlgdx/xsks/xsksap_query?Ves632DSdyV=NEW_XSD_KSBM')
        content = r.text
        term = re.search(r"<option selected value=\".*?\">(?P<term>.*?)</option>", content, re.S).group('term')
        return term
    now = datetime.datetime.now()
    key = '{0}/{1}'.format(now.year, now.month)
    data = cache.get(key)
    if data:
        return data
    else:
        cache.set(key, fetch_curent_term())
        return cache.get(key)

get_current_term()
print('获取当前学期:\n{0}'.format(get_current_term()))


def jwc_hash_key(username, password):
    if isinstance(password, unicode_type):
        password = password.encode('utf-8')
    return username + md5(password).hexdigest().upper()


@gen.coroutine
def async_fetch(url, headers=None, method="GET", data=None, follow_redirects=False):
    """
    Async http fetch
    :param url:
    :param headers:
    :param method:
    :param data:
    :param follow_redirects:
    """
    client = HTTPClient()
    headers = headers or {}
    body = None
    if method == "GET" and data is not None:
        url = url + '?' + urlencode(data)
    elif method == "POST" and data is not None:
        headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
        body = urlencode(data)
    request = HTTPRequest(url=url, headers=headers,
                          method=method, follow_redirects=follow_redirects,
                          body=body)
    response = yield client.fetch(request, raise_error=False)
    # return response
    raise gen.Return(response)


@gen.coroutine
def async_login_session(username, password, from_cache=True):
    key = jwc_hash_key(username, password)
    if from_cache:
        cookie = cache.get(key)
        if cookie:
            print('use cookie from cache')
            # return cookie
            raise gen.Return(cookie)
    else:
        cache.remove(key)
    login_url = jwc_domain + '/njlgdx/xk/LoginToXk'
    response = yield async_fetch(login_url,
                                 headers={'Connection': 'Keep-alive'},
                                 method="GET",
                                 data=login_data(username, password))
    if len(response.body) > 0:
        # 密码错误之类的错误
        # return None
        raise gen.Return(None)
    else:
        # 成功请求会返回一个空的body (wtf??)
        cookie = response.headers.get('Set-Cookie', '').split(';')[0]
        cache.set(key, cookie)
        print('set cookie')
        print(key, ' -> ', cookie)
        # return cookie
        raise gen.Return(cookie)


@gen.coroutine
def async_content(username, password, path, headers=None, method="GET", data=None):
    """ 异步请求内容, 可以是GET或者POST, 参数使用字典data表示
    :param username:
    :param password:
    :param path:
    :param method:
    :param data:
    :return:
    """
    res = dict(status="error", data="")
    cookie = yield async_login_session(username, password)
    if cookie is None:
        # 经过验证, 这个帐号密码不对
        res["status"] = "error"
        res["data"] = u"用户名或密码错误"
        # return res
        raise gen.Return(res)
    url = jwc_domain + path
    headers = headers or {}
    headers['Cookie'] = cookie
    # http_client = HTTPClient()
    # request = HTTPRequest(url=url, headers={'Cookie': cookie},
    #                       method="GET", follow_redirects=False)
    response = yield async_fetch(url, headers=headers, method=method, data=data)
    try:
        # 成功解析, 编码将是utf-8
        res["data"] = response.body.decode('utf-8')
        res["status"] = "success"
    except UnicodeDecodeError as e:
        # 未登录, jwc报错, 编码将是gbk(wtf??)
        # 缓存中读出的cookie已经失效 (如果密码真错了而且没走缓存, cookie返回None)
        # 使缓存失效, 再请求一次session, 结果是啥就是啥
        print('use cookie in cache fail!')
        cookie = yield async_login_session(username, password, from_cache=False)
        print('get new cookie', cookie)
        if cookie is None:
            res["status"] = "error"
            res["data"] = "用户名或密码错误"
        else:
            headers['Cookie'] = cookie
            response = yield async_fetch(url, headers=headers, method=method, data=data)
            try:
                res["data"] = response.body.decode('utf-8')
                res["status"] = "success"
            except Exception:
                res["status"] = "error"
                res["data"] = "未知错误"
    # return res
    raise gen.Return(res)


@gen.coroutine
def async_get_score(username, password):
    res = yield async_content(username, password, '/njlgdx/kscj/cjcx_list')
    # 在Python3中支持return语句, 而Python2只能这样
    raise gen.Return(res)


@gen.coroutine
def async_post_exam(username, password, term):
    data = dict(xnxqid=term)
    res = yield async_content(username, password, '/njlgdx/xsks/xsksap_list',
                              method="POST", data=data)
    raise gen.Return(res)


@gen.coroutine
def async_get_info(username, password):
    res = yield async_content(username, password, '/njlgdx/grxx/xsxx')
    raise gen.Return(res)


# 默认的行处理函数, 用于查询成绩, 考试中的dataList处理
default_row2list = lambda r: [unicode_type(d.string) or '' for d in r.contents if not(isinstance(d, bs4.element.NavigableString) and d.isspace())]
default_head2list = default_row2list


def traverse_table(table_tag, head2list=None, row2list=None):
    res = dict()
    if head2list is None:
        head2list = default_head2list
    if row2list is None:
        row2list = default_row2list
    table = iter(table_tag.contents)
    for row in table:
        if isinstance(row, bs4.element.NavigableString):
            continue
        res["head"] = head2list(row)
        break
    res["body"] = []
    for row in table:
        if not isinstance(row, bs4.element.NavigableString):
            res["body"].append(row2list(row))
    return res
    