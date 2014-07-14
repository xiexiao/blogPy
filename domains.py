# -*- coding: utf-8 -*-

from sqlalchemy import Table,Column,Integer,String,Boolean
from sqlalchemy import ForeignKey,MetaData,Text,DateTime
from sqlalchemy import Unicode,UnicodeText
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref, relationship
import datetime

metadata = MetaData()
Base = declarative_base()
Base.metadata = metadata

'''
Item categories
'''
class ItemCat(Base):
  __tablename__ = 'x_itemcat'

  id = Column(Integer, primary_key=True) #autoincrement=False
  name = Column(Unicode(30), nullable=False)
  beta = Column(Unicode(30), nullable=False, unique=True)
  orders = Column(Integer, nullable=False)
  keyword = Column(Unicode(200), nullable=True)
  description = Column(Unicode(300), nullable=True)
  ishide = Column(Boolean, nullable = False)

  def __init__(self, name, beta, orders, keyword, description, ishide):
    self.name = name
    self.beta = beta
    self.orders = orders
    self.keyword = keyword
    self.description = description
    self.ishide = False

  def __repr__(self):
    return "<ItemCat('%s','%s','%s')>" % (self.id, self.name, self.beta)


'''
Item
'''
class Item(Base):
  __tablename__ = 'x_item'

  id = Column(Integer, primary_key=True, autoincrement=True)
  beta = Column(Unicode(100), nullable=False, unique=True)
  title = Column(Unicode(100), nullable=False)
  content = Column(UnicodeText, nullable=False)
  adddate = Column(DateTime, nullable=False)
  ispass = Column(Boolean, nullable = False)
  pubdate = Column(DateTime, nullable=False)

  #ItemCat
  itemcat_id = Column(Integer, ForeignKey('x_itemcat.id'),nullable = False)
  itemcat = relation(ItemCat, backref=backref('items',order_by=id))

  def __init__(self, beta, title, content, adddate, pubdate, ispass ):
    self.beta = beta
    self.title = title
    self.content = content
    self.adddate = adddate

    self.pubdate = pubdate
    self.ispass = ispass

  def __repr__(self):
    return "<Item('%s','%s')>" % (self.id, self.title)

'''
Item comment
'''
class ItemComment(Base):
  __tablename__ = 'x_itemcomment'

  id = Column(Integer, primary_key=True)
  username = Column(String(10), nullable=False)
  mail = Column(String(50), nullable=False)
  site = Column(String(50), nullable=True)
  content = Column(String(800), nullable=False)
  adddate = Column(DateTime, nullable=False)
  ip = Column(String(50), nullable=False)
  ispass = Column(Boolean, nullable=False)
  isshowsite = Column(Boolean, nullable=False)

  #Item
  item_id = Column(Integer, ForeignKey('x_item.id'), nullable = False)
  item = relation(Item, backref=backref('comments', order_by=id))

  def __init__(self, username, mail, content, adddate, ip, item_id ):
    self.username = username
    self.mail = mail
    self.content = content
    self.adddate = adddate
    self.ip = ip
    self.item_id = item_id
    self.ispass = False
    self.isshowsite = False

#===============================
# this for create database
#===============================


def getItems(fileName):
  import codecs
  f = codecs.open(fileName,'r','utf-8')
  content = f.read()
  f.close()
  content = content[content.index('{'):]
  import json
  b = json.loads(content)
  return b['items']

if __name__ == '__main__':
  import sys
  reload(sys)
  sys.setdefaultencoding('utf-8')

  from sqlalchemy import create_engine
  engine = create_engine('sqlite:///blog_beta.db',
      #connect_args={'charset':'utf8',},
      #assert_unicode=True,
      convert_unicode=True,
      encoding='utf-8',
      echo=True)
  #create database
  metadata.create_all(engine)

  from sqlalchemy.orm import sessionmaker
  Session = sessionmaker(bind=engine)
  session = Session()

  #create datas
  c = "test"
  itemcat = ItemCat(c, c, 1, c, c, False)
  session.add(itemcat)
  session.commit()

  from datetime import datetime
  ispass = True
  title = u'test'
  content = u'test'

  pubDate = datetime.utcnow()

  item_beta = "test"
  itemi = Item(item_beta, title,content,
      pubDate, pubDate, ispass)
  itemi.itemcat = itemcat
  session.add(itemi)
  session.flush()

  session.commit()
  session.close()
  raw_input()
