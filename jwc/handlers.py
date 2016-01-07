#!/usr/bin/env python
# encoding: utf-8

from hashlib import md5
import re

import tornado.web
import tornado.httpclient
import requests

http_root = 'http://202.119.81.112:9080'

class JWCInfoHandler(tornado.web.RequestHandler):
    def get(self):
        data = {
            'method': 'verify',
            'USERNAME': self.get_argument("sid"),
            'PASSWORD': md5(self.get_argument("pwd")).hexdigest().upper()
        }
        #http = tornado.httpclient.HTTPClient()
        http = requests.Session()
        res = http.get(http_root+'/njlgdx/xk/LoginToXk', params=data)
        if re.search(u'退出', res.text):
            res = http.get(http_root+'/njlgdx/grxx/xsxx')
            res.encoding = 'utf-8'
            patt = r'''
            <table\s*id=\"xjkpTable\".*?>\s*<tr.*?>.*?</tr>\s*<tr.*?>.*?</tr>\s*
            <tr.*?>\s*
            <td.*?>(?P<college>.*?)</td>\s*
            <td.*?>(?P<major>.*?)</td>\s*
            <td.*?>.*?</td>\s*
            <td.*?>(?P<class>.*?)</td>
            .*?</tr>\s*
            <tr.*?>\s*
            <td.*?>.*?</td>\s*
            <td.*?>(?P<name>.*?)</td>
            .*?</tr>\s*
            <tr.*?>.*?</tr>\s*
            <tr.*?>\s*
            <td.*?>.*?</td>\s*
            <td.*?>(?P<subject>.*?)</td>
            .*?</tr>
            '''
            p = re.compile(patt, re.DOTALL | re.MULTILINE | re.VERBOSE)
            result = p.search(res.text)
            self.write((result.group('name')) + '<br/>')
            self.write((result.group('class')) + '<br/>')
            self.write((result.group('college')) + '<br/>')
            self.write((result.group('major')) + '<br/>')
            self.write((result.group('subject')) + '<br/>')
