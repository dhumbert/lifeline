#!/usr/bin/env python2.7

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, options
from lifeline import app


define("port", default=5999, help="run on the given port", type=int)
options.parse_command_line()

http_server = HTTPServer(WSGIContainer(app))
http_server.listen(options.port)
IOLoop.instance().start()