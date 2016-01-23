#!/usr/bin/env python
# encoding: utf-8

from hashlib import md5
import re

import tornado.web
import tornado.httpclient
import requests
from bs4 import BeautifulSoup
import ujson

jwc_domain = 'http://202.119.81.112:9080'


def login_session(username, password):
    data = {
        'method': 'verify',
        'USERNAME': username,
        'PASSWORD': md5(password).hexdigest().upper()
    }
    http = requests.Session()
    res = http.get(jwc_domain + '/njlgdx/xk/LoginToXk', params=data)
    if re.search(u'退出', res.text):
        return http


class StudentInfoHandler(tornado.web.RequestHandler):
    def get(self):
        data = {
            'method': 'verify',
            'USERNAME': self.get_argument("user"),
            'PASSWORD': md5(self.get_argument("pwd")).hexdigest().upper()
        }
        http = requests.Session()
        res = http.get(jwc_domain+'/njlgdx/xk/LoginToXk', params=data)
        if re.search(u'退出', res.text):
            res = http.get(jwc_domain+'/njlgdx/grxx/xsxx')
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


class ScoreHandlers(tornado.web.RequestHandler):
    def get(self):
        user, pwd = map(self.get_argument, ['user', 'pwd'])
        http = login_session(user, pwd)
        score_page = http.get(jwc_domain + '/njlgdx/kscj/cjcx_list')
        soup = BeautifulSoup(score_page.text)
        res = {}
        table = soup.find(id='dataList')
        for row in table.contents[3::2]:
            ro = []
            term = unicode(row.contents[3].string)
            for col in row.contents[5::2]:
                ro.append(unicode(col.string))
            res.setdefault(term, [])
            res[term].append(ro)
        self.write(ujson.dumps(res, sort_keys=True))
