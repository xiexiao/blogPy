# -*- coding: utf-8 -*-

import os
import sys
curdir = os.path.dirname(__file__)
sys.path.append(curdir)
os.environ['PYTHON_EGG_CACHE']="/tmp"

import web
from web.contrib.template import render_mako
from util import StaticDirHandler
from util import StaticFileHandler

urls = (
    '/', 'Index',
    '/favicon.ico', 'Ico',
    '/page/([0-9]{1,6})','Index',
    '/page/([0-9]{1,6})/','Index',

    '/rss', 'RssIndex',
    '/rss/', 'RssIndex',

    '/([^.///?]+)','ItemDetail',
    '/([^.///?]+)/','ItemDetail',
    '/([^.///?]+)/([0-9]{1,6})','ItemDetail',
    '/([^.///?]+)/([0-9]{1,6})/','ItemDetail',

    '/category/([^.///?]+)','ClassList',
    '/category/([^.///?]+)/','ClassList',
    '/category/([^.///?]+)/page/([0-9]{1,6})/','ClassList',

    '/admin/catlist', 'AdminCatList',
    '/admin/catlist/', 'AdminCatList',
    '/admin/catlist/([0-9]{1,6})','AdminCatList',
    '/admin/catlist/([0-9]{1,6})/','AdminCatList',
    '/admin/catlist/delete/([0-9]{1,6})/','AdminCatDel',

    '/admin/itemlist', 'AdminItemList',
    '/admin/itemlist/', 'AdminItemList',
    '/admin/itemlist/([0-9]{1,6})','AdminItemList',
    '/admin/itemlist/([0-9]{1,6})/','AdminItemList',

    '/admin/commentlist', 'AdminCommentList',
    '/admin/commentlist/', 'AdminCommentList',
    '/admin/commentlist/([0-9]{1,6})','AdminCommentList',
    '/admin/commentlist/([0-9]{1,6})/','AdminCommentList',
    '/admin/commentpass/([0-9]{1,6})/','AdminCommentPass',

    '/admin/itemedit','AdminItemEdit',
    '/admin/itemedit/','AdminItemEdit',

    '/admin/itemedit/([0-9]{1,6})','AdminItemEdit',
    '/admin/itemedit/([0-9]{1,6})/','AdminItemEdit',
    )

from pages import *

app = web.application(urls, globals())

def my_processor(handler):
  if web.ctx.env['PATH_INFO'] and web.ctx.env['PATH_INFO'].lower() != web.ctx.env['PATH_INFO'] :
    web.ctx.home = web.ctx.home.encode('utf-8') #when chinese path 
    web.seeother(web.ctx.env['PATH_INFO'].lower())
    return
  result = handler()
  return result

app.add_processor(my_processor)

if __name__ == '__main__':
  #web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
  app.run()

