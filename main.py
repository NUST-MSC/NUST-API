#!/usr/bin/env python
# encoding: utf-8

import os
import re
import configparser

from tornado.options import define, options
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.autoreload

import jwc.handlers

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=True, help="debug Mode", type=bool)
config = configparser.ConfigParser()

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/u/info', jwc.handlers.StudentInfoHandler),
            (r'/u/score', jwc.handlers.ScoreHandlers),
        ]
        try:
            config.read('app.conf')
        except Exception:
            print('wrong')
            exit(0)
        settings = dict(
            debug = options.debug,
            cookie_secret = config['default']['cookie_secret'],
            session_secret = config['default']['session_secret'],
            login_url = '/forbiden',
        )
        tornado.web.Application.__init__(self, handlers, **settings)

if __name__ == '__main__':
    tornado.options.parse_command_line()
    #connect(options.mongo_database, host=options.mongo_host)
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    instance = tornado.ioloop.IOLoop.instance()
    tornado.autoreload.start(instance)
    instance.start()
