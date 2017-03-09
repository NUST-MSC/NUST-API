#!/usr/bin/env python
# encoding: utf-8

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

try:
    config.read('app.conf')
except Exception:
    print('Wrong when parse app.conf')
    exit(0)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/jwc/info', jwc.handlers.StudentInfoHandler),
            (r'/jwc/score', jwc.handlers.ScoreHandler),
            (r'/jwc/exam', jwc.handlers.ExamHandler),
        ]
        settings = dict(
            debug=options.debug,
            cookie_secret=config['default']['cookie_secret'],
        )
        tornado.web.Application.__init__(self, handlers, **settings)

if __name__ == '__main__':
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    instance = tornado.ioloop.IOLoop.instance()
    tornado.autoreload.start(instance)
    instance.start()
