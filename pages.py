# -*- coding:utf-8 -*-

import os
import web
import math
import datetime
import time
import urllib

from util import render_mako
from util import StaticDirHandler
from util import StaticFileHandler

def localtime(d):
  return d + datetime.timedelta(seconds=28800)

def gmttime(d):
  return d - datetime.timedelta(seconds=28800)

curdir = os.path.dirname(__file__)

#Mako templates
render = render_mako(
  directories=[os.path.join(curdir, 'templates').replace('\\','/'),],
           input_encoding='utf-8',
           output_encoding='utf-8',)

#connect to db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, subqueryload, contains_eager
engine = create_engine('sqlite:///%s/blog_beta.db'%curdir, convert_unicode=True,
      encoding='utf-8',
      echo=True,
      )
Session = sessionmaker(bind=engine)

#ORM domains
from domains import *
import config

import markupsafe
def myhtml(text):
  tempText = markupsafe.escape(text)
  return ('%s' % tempText).replace('\n','<br />')

def LoadInfo():
  d = {}
  d['localtime'] = localtime
  d['site_url'] = config.site_url
  d['site_generator'] = config.site_generator
  d['site_name'] = config.site_name;
  d['site_subname'] = config.site_subname;
  d['site_title'] = config.site_name + ' - ' + config.site_subname;
  d['site_keywords'] = config.site_keywords;
  d['site_description'] = config.site_description; 
  d['myhtml'] = myhtml; 

  #get latest items
  session = Session()
  try:
    d['catlist'] = session.query(ItemCat).\
              order_by(ItemCat.orders.asc()).\
              all()
    d['newitemlist'] =  session.query(Item).\
          join(Item.itemcat).\
          filter(Item.pubdate < datetime.datetime.utcnow() ).\
          filter(Item.ispass == True).\
          options(contains_eager(Item.itemcat)).\
          order_by(Item.pubdate.desc())\
          [:15]
    d['newcommentlist'] =  session.query(ItemComment).\
          join(ItemComment.item).\
          filter(Item.pubdate < datetime.datetime.utcnow() ).\
          filter(ItemComment.ispass == True).\
          options(contains_eager(ItemComment.item)).\
          order_by(ItemComment.adddate.desc())\
          [:15]
  finally:
    session.close()
  return d

def GetClass(className, startIndex = 0, pageSize = 25, session = None):
  needClose = False
  if not session:
    needClose = True
    session = Session()
  try:
    return session.query(Item).\
        join(Item.itemcat).\
        filter(ItemCat.beta == className.lower()).\
        filter(Item.pubdate < datetime.datetime.utcnow() ).\
        options(contains_eager(Item.itemcat)).\
        order_by(Item.pubdate.desc())\
        [startIndex:startIndex+pageSize]
  finally:
    if needClose:
      session.close()

#class list 
class ClassList:
  def GET(self, className, page = 1):
    d = LoadInfo()
    session = Session()
    d['recodecount'] = 0
    d['pagecount'] = 0
    page = int(page)
    pageSize = 5

    startIndex = pageSize*(page-1)
    d['itemlist'] = GetClass(className, startIndex , pageSize)

    if web.ctx.env.get('HTTP_HOST','').startswith('localhost'):
      d['debug'] = True
    if(d['itemlist']):
      d['itemCat'] = d['itemlist'][0].itemcat
      if page==0: page=1
      d['recodecount'] = session.query(Item).\
          filter(Item.pubdate < datetime.datetime.utcnow() ).\
          filter(Item.itemcat_id == d['itemCat'].id).count()
      d['pagecount'] =  int(math.ceil( d['recodecount'] / float(pageSize)))
      if d['pagecount']==0: d['pagecount']=1
    else:
      try:
        d['recodecount'] = 0
        d['pagecount'] = 0
        d['itemCat'] = session.query(ItemCat).\
          filter(ItemCat.beta == className.lower()).\
          first();
      finally:
        session.close()

    if d.has_key('itemCat') and d['itemCat']:
      d['site_title'] = u'%s-%s:第%s页' % (d['itemCat'].name, config.site_name, page)
      d['site_keywords'] = d['itemCat'].name
      d['site_description'] = d['itemCat'].name + u'相关'
      d['page'] = page
      return render.classify(**d)
    return web.notfound(self)#not found

def quote_u(a):
  return urllib.quote(a.encode('utf-8'))

#item detail
class ItemDetail:
  def GET(self, itembeta, page=1):
    d = LoadInfo()
    session = Session()
    try:
      d['item'] = session.query(Item).\
        join(Item.itemcat).\
        filter(Item.pubdate < datetime.datetime.utcnow() ).\
        filter(Item.beta == itembeta).\
        filter(Item.ispass == True).\
        options(contains_eager(Item.itemcat)).\
        first()

      if(d['item']):
        d['site_title'] = d['item'].title + config.site_name;
        d['site_description'] = d['item'].content[:100];

        d['recodecount'] = 0
        d['pagecount'] = 0
        page = int(page)
        pageSize = 10

        startIndex = pageSize*(page-1)

        #comment total
        d['commentcount'] =  session.query(ItemComment).\
          join(ItemComment.item).\
          filter(ItemComment.item_id == d['item'].id).\
          options(contains_eager(ItemComment.item)).\
          count()

        d['page'] = 0
        if d['commentcount'] and d['commentcount'] > 0:
          #comment list
          d['commentlist'] =  session.query(ItemComment).\
            join(ItemComment.item).\
            options(contains_eager(ItemComment.item)).\
            filter(ItemComment.item_id == d['item'].id).\
            filter(ItemComment.ispass == True).\
            order_by(ItemComment.adddate.desc())\
            [startIndex:startIndex+pageSize]
          if page==0: page=1
          d['pagecount'] =  int(math.ceil( d['commentcount'] / float(pageSize)));
          if d['pagecount']==0: d['pagecount']=1
          d['page'] = page

        if web.ctx.env.get('HTTP_HOST','').startswith('localhost'):
          d['debug'] = True

        return render.details(**d)
    finally:#end try
      session.close()
    return web.notfound(self)#not found

  def POST(self, itembeta, page=0):
    d = LoadInfo()
    i = web.input()
    if not i.author.strip():
      d['msg'] = u'<p style="color:red">名字必须填写!</p>'
      return render.msgshow(**d)
    if not i.email.strip():
      d['msg'] = u'<p style="color:red">邮箱必须填写!</p>'
      return render.msgshow(**d)
    if not i.comment.strip():
      d['msg'] = u'<p style="color:red">评论内容必须填写!</p>'
      return render.msgshow(**d)
    session = Session()
    try:
      itemv = session.query(Item).\
        filter(Item.pubdate < datetime.datetime.utcnow() ).\
        filter(Item.beta == itembeta).\
        first()
      ip = web.ctx.ip
      comment1 = ItemComment(i.author, i.email, i.comment, datetime.datetime.utcnow(), ip, itemv.id)
      session.add(comment1)
      session.commit()
    finally:
      session.close()
    d['msg'] = u'<h1>保存成功!</h1>'
    return render.msgshow(**d)

#main index
class Index:
  def GET(self, page = 1 ):
    d = LoadInfo()
    pageSize = 5
    page = int(page)
    startIndex = pageSize*(page-1)
    session = Session()
    try:
      d['itemlist'] =  session.query(Item).\
        join(Item.itemcat).\
        filter(Item.pubdate < datetime.datetime.utcnow() ).\
        filter(Item.ispass == True).\
        options(contains_eager(Item.itemcat)).\
        order_by(Item.pubdate.desc())\
        [startIndex:startIndex+pageSize]
      if page==0: page=1
      #total
      d['recodecount'] =  session.query(Item).\
        join(Item.itemcat).\
        filter(Item.pubdate < datetime.datetime.utcnow() ).\
        filter(Item.ispass == True).\
        options(contains_eager(Item.itemcat)).\
        count()
      d['pagecount'] =  int(math.ceil( d['recodecount'] / float(pageSize)));
      if d['pagecount']==0: d['pagecount']=1
      d['page'] = page
      d['itemcat'] = session.query(ItemCat).all()
    finally:
      session.close()
    #local not show stat
    if web.ctx.env.get('HTTP_HOST','').startswith('localhost'):
      d['debug'] = True
    return render.index(**d)

#Rss page
class RssIndex:
  def GET(self):
    d = LoadInfo()
    #web.header('Content-Type','text/xml; charset=utf-8', unique=True)
    #web.header('Transfer-Encoding', 'chunked')
    d['now'] = datetime.datetime.utcnow()
    session = Session()
    try:
      pageSize = 20
      d['itemlist'] = session.query(Item).\
        filter(Item.pubdate < datetime.datetime.utcnow() ).\
        filter(Item.ispass == True).\
        join(Item.itemcat).\
        options(subqueryload('itemcat')).\
        order_by(Item.pubdate.desc())\
        [:pageSize]
    finally:
      session.close()
    return render.rss(**d)

class Ico(StaticFileHandler):
  file_path = "favicon.ico"
  content_type = "image/vnd.microsoft.icon"

class AdminCatDel:
  def GET(self,catid=0):
    d = LoadInfo()
    if catid == 0:
      d['msg'] = u'<h1>找不到该分类</h1>'
      d['returnurl'] = u'/admin/catlist/'
      return render.msgshow(**d)
    session = Session()
    try:
      catcount =session.query(Item).\
        join(Item.itemcat).\
        filter(ItemCat.id == int(catid)).\
        options(contains_eager(Item.itemcat)).\
        count()
    finally:
      session.close()
    if catcount:
      d['msg'] = u'<h1>分类下还有文章,不能删除!</h1>'
      d['returnurl'] = u'/admin/catlist/'
      return render.msgshow(**d)
    else:
      #delete 
      catitems = [x for x in d['catlist'] if int(x.id)==int(catid)]
      if catitems:
        session = Session()
        try:
          session.delete(catitems[0])
          session.commit()
        finally:
          session.close()
        d['msg'] = u'<h1>删除成功</h1>'
        d['returnurl'] = u'/admin/catlist/'
        return render.msgshow(**d)
      else:
        d['msg'] = u'<h1>找不到该分类</h1>'
        d['returnurl'] = u'/admin/catlist/'
        return render.msgshow(**d)

class AdminCatList:
  def GET(self, catid=0):
    d = LoadInfo()
    d['myitem'] = ""
    if d['catlist']:
      if catid>0:
        catitems = [x for x in d['catlist'] if int(x.id)==int(catid)]
        if catitems:
          d['myitem'] = catitems[0]
      return render.admin_catlist(**d)
    return web.notfound(self)

  def POST(self):
    d = LoadInfo()
    i = web.input()
    if not i.myid.strip():
      d['msg'] = u'<p style="color:red">id必须填写!</p>'
      return render.msgshow(**d)
    if not i.mname.strip():
      d['msg'] = u'<p style="color:red">名字必须填写!</p>'
      return render.msgshow(**d)
    if not i.mbeta.strip():
      d['msg'] = u'<p style="color:red">beta必须填写!</p>'
      return render.msgshow(**d)
    if not i.morders.strip():
      d['msg'] = u'<p style="color:red">orders必须填写!</p>'
      return render.msgshow(**d)
    session = Session()
    try:
      myid = int(i.myid)
      name = i.mname.strip()
      beta = i.mbeta.strip()
      orders = int(i.morders.strip())
      keyword = i.mkeyword.strip()
      description = i.mdescription.strip()
      ishide = i.mishide.strip() == 'true'
      if myid !=0:
        itemv = session.query(ItemCat).\
          filter(ItemCat.id == myid).\
          first()
        itemv.name = name
        itemv.beta = beta
        item.orders = orders
        item.keyword = keyword
        item.description = description
        item.ishide = ishide
      else:
        itemv = ItemCat(name, beta, orders, keyword, description, ishide)
      session.add(itemv)
      session.commit()
    finally:
      session.close()
    d['msg'] = u'<h1>保存成功!</h1>'
    d['returnurl'] = u'/admin/catlist/'
    return render.msgshow(**d)

class AdminItemList:
  def GET(self, page = 1 ):
    d = LoadInfo()
    pageSize = 20
    page = int(page)
    startIndex = pageSize*(page-1)
    session = Session()
    try:
      d['itemlist'] =  session.query(Item).\
        join(Item.itemcat).\
        options(contains_eager(Item.itemcat)).\
        order_by(Item.pubdate.desc())\
        [startIndex:startIndex+pageSize]
      if page==0: page=1
      #总数
      d['recodecount'] =  session.query(Item).\
        join(Item.itemcat).\
        options(contains_eager(Item.itemcat)).\
        count()
      d['pagecount'] =  int(math.ceil( d['recodecount'] / float(pageSize)));
      if d['pagecount']==0: d['pagecount']=1
      d['page'] = page
      d['itemcat'] = session.query(ItemCat).all()
    finally:
      session.close()
    return render.admin_itemlist(**d)

class AdminCommentList:
  def GET(self, page = 1 ):
    d = LoadInfo()
    pageSize = 20
    page = int(page)
    startIndex = pageSize*(page-1)
    session = Session()
    try:
      d['commentlist'] =  session.query(ItemComment).\
        options(contains_eager(ItemComment.item)).\
        order_by(ItemComment.adddate.desc())\
        [startIndex:startIndex+pageSize]
      if page==0: page=1
      #总数
      d['recodecount'] =  session.query(ItemComment).\
        options(contains_eager(ItemComment.item)).\
        count()
      d['pagecount'] =  int(math.ceil( d['recodecount'] / float(pageSize)));
      if d['pagecount']==0: d['pagecount']=1
      d['page'] = page
    finally:
      session.close()
    return render.admin_commentlist(**d)

class AdminItemEdit:
  def GET(self, itemid = 0 ):
    d = LoadInfo()
    session = Session()
    try:
      d['myitem'] =  session.query(Item).\
          filter(Item.id == int(itemid)).\
          first()
    finally:
      session.close()
    if not d['myitem']:
      d['myitem'] = Item('', '', '', datetime.datetime.utcnow(), datetime.datetime.utcnow(), False)
      d['myitem'].id = 0
    return render.admin_itemedit(**d)

  def POST(self, itemid = 0):
    d = LoadInfo()
    i = web.input()
    if not i.myid.strip():
      d['msg'] = u'<p style="color:red">id必须填写!</p>'
      return render.msgshow(**d)
    if not i.mtitle.strip():
      d['msg'] = u'<p style="color:red">title必须填写!</p>'
      return render.msgshow(**d)
    if not i.mbeta.strip():
      d['msg'] = u'<p style="color:red">beta必须填写!</p>'
      return render.msgshow(**d)
    if not i.mcategory.strip():
      d['msg'] = u'<p style="color:red">category必须填写!</p>'
      return render.msgshow(**d)
    session = Session()
    try:
      itemv = Item(None, None, None, None, None, None)
      if int(i.myid)!=0:
        itemv = session.query(Item).\
          filter(Item.id == int(i.myid)).\
          first()
      itemv.title = i.mtitle.strip()
      itemv.beta = i.mbeta.strip()

      catitems = [x for x in d['catlist'] if int(x.id)==int(i.mcategory)]
      if catitems:
        itemv.itemcat = catitems[0]
      else:
        itemv.itemcat = d['catlist'][0]
      fmr = '%Y-%m-%d %H:%M:%S'

      adddate = time.strptime(i.madddate.strip(), fmr)
      adddate = gmttime(datetime.datetime(*adddate[:6]))
      itemv.adddate = adddate

      pubdate = time.strptime(i.mpubdate.strip(), fmr)
      pubdate = gmttime(datetime.datetime(*pubdate[:6]))
      itemv.pubdate = pubdate
      itemv.ispass = i.mispass.strip() == 'true'
      itemv.content = i.mcontent.strip()
      session.add(itemv)
      session.commit()
    finally:
      session.close()
    if int(i.myid)==0:
      d['msg'] = u'<h1>添加成功!</h1>'
    else:
      d['msg'] = u'<h1>修改保存成功!</h1>'
    d['returnurl'] = u'/admin/itemlist/'
    return render.msgshow(**d)

class AdminCommentPass:
  def GET(self, cid=0):
    d = LoadInfo()
    if cid == 0:
      d['msg'] = u'<h1>找不到该评论</h1>'
      d['returnurl'] = u'/admin/commentlist/'
      return render.msgshow(**d)
    session = Session()
    #delete 
    try:
      comment =  session.query(ItemComment).\
        filter(ItemComment.id == int(cid)).\
        first()
      if comment:
        comment.ispass = not comment.ispass
        session.add(comment)
        session.commit()
        d['msg'] = u'<h1>修改成功</h1>'
        d['returnurl'] = u'/admin/commentlist/'
      else:
        d['msg'] = u'<h1>找不到该评论</h1>'
        d['returnurl'] = u'/admin/commentlist/'
      return render.msgshow(**d)
    finally:
      session.close()
