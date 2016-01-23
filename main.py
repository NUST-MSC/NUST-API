#!/usr/bin/env python
# encoding: utf-8

import os
import re
from tornado.options import define, options
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.autoreload

import jwc.handlers

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=True, help="Debug Mode", type=bool)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/u/info', jwc.handlers.StudentInfoHandler),
            (r'/u/score', jwc.handlers.ScoreHandlers),
        ]
        settings = dict(
            # template_path = os.path.join(os.path.dirname(__file__), "templates"),
            # static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug = options.debug,
            # xsrf_cookies = True,
            cookie_secret = "81o0TzKaPpGtYdkL5gEmGepeuuYi7EPnp2XdTP1o&Vo=",
            login_url = "/forbiden",
            session_secret = 't43213&^(01',
            # session_dir=os.path.join(os.path.dirname(__file__), "tmp/session"),
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
