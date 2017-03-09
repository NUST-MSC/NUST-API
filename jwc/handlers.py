#!/usr/bin/env python
# encoding: utf-8

import re
import json
from collections import OrderedDict
from hashlib import md5

from tornado import gen
import requests
from bs4 import BeautifulSoup

from interface import BaseHandler
from jwc.util import async_get_info, async_get_score, async_post_exam
from jwc.util import traverse_table
from jwc.util import get_class_sys_data, get_current_term

jwc_domain = 'http://202.119.81.112:9080'


def login_session(username, password):
    data = {
        'method': 'verify',
        'USERNAME': username.encode('utf-8'),
        'PASSWORD': md5(password.encode('utf-8')).hexdigest().upper()
    }
    http = requests.Session()
    res = http.get(jwc_domain + '/njlgdx/xk/LoginToXk', params=data)
    if re.search(u'退出', res.text):
        return http


class StudentInfoHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        user, pwd = map(self.get_argument, ["user", "pwd"])
        res = yield async_get_info(user, pwd)
        if res["status"] == "error":
            self.send_error(400)
            self.write(res["data"])
            self.finish()
            return
        patt = r'''
        <table\s*id=\"xjkpTable\".*?>\s*<tr.*?>.*?</tr>\s*<tr.*?>.*?</tr>\s*
        <tr.*?>\s*
        <td.*?>院系：(?P<college>.*?)</td>\s*
        <td.*?>专业：(?P<major>.*?)</td>\s*
        <td.*?>.*?</td>\s*
        <td.*?>班级：(?P<class>.*?)</td>\s*
        <td.*?>学号：(?P<studentID>.*?)</td>\s*
        .*?</tr>\s*
        <tr.*?>\s*
        <td.*?>.*?</td>\s*
        <td.*?>&nbsp;(?P<name>.*?)</td>\s*
        <td.*?>.*?</td>\s*
        <td.*?>&nbsp;(?P<gender>.*?)</td>\s*
        .*?</tr>\s*
        <tr.*?>.*?</tr>\s*
        <tr.*?>\s*
        <td.*?>.*?</td>\s*
        <td.*?>&nbsp;(?P<subject>.*?)</td>
        .*?</tr>
        '''
        print(res)
        p = re.compile(patt, re.DOTALL | re.MULTILINE | re.VERBOSE)
        result = p.search(res["data"])
        res = {
            'name': result.group('name'),
            'class': result.group('class'),
            'college': result.group('college'),
            'major': result.group('major'),
            'subject': result.group('subject'),
            'studentID': result.group('studentID'),
            'gender': result.group('gender')
        }
        self.write(res)


class ScoreHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        user, pwd = map(self.get_argument, ['user', 'pwd'])
        res = yield async_get_score(user, pwd)
        if res["status"] == "error":
            self.send_error(400)
            self.finish(res["data"])
            return
        content = res["data"]
        soup = BeautifulSoup(content.replace('\n', ''))
        table_tag = soup.find(id="dataList")
        table = traverse_table(table_tag)
        print(table)
        res = {}
        class_ids = set()
        for row in table["body"]:
            term = row[1]
            res.setdefault(term, [])
            res[term].append(row[2:])   # 学期不要
            try:
                # 如果过了就把课序号插入到ids里, 可以解耦.. 先这吧
                if float(row[4]) >= 60.0:
                    class_ids.add(row[2])
            except ValueError:
                if row[4] in [u'优秀', u'良好', u'中等', u'及格']:
                    class_ids.add(row[2])
        res = OrderedDict(sorted(res.items(), key=lambda x: x[0], reverse=True))
        syss = ['foreign', 'humanity', 'science']
        class_sys = {k: [] for k in syss}
        class_sys_data = get_class_sys_data()
        for id in class_ids:
            for sys in syss:
                if id in class_sys_data.get(sys, {}):
                    class_item = class_sys_data[sys][id].copy()
                    class_item.update({'id': id})
                    class_sys[sys].append(class_item)
        self.write({'scores': res, 'classSys': class_sys})


class ExamHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        user, pwd = map(self.get_argument, ['user', 'pwd'])
        current_term = get_current_term()
        res = yield async_post_exam(user, pwd, current_term)
        if res["status"] == "error":
            self.send_error(400)
            self.finish(res["data"])
            return
        soup = BeautifulSoup(res["data"])
        table = traverse_table(soup.find(id="dataList"))
        self.write(json.dumps(table["body"]))
