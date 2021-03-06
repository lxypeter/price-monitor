# -*- coding: utf-8 -*-

'''
application's models and database method
'''

__author__ = 'CY Lee'

import logging
import time
import uuid
import json
from enum import Enum, unique
from flask import g
import pymysql.cursors
import redis
from config.config import CONFIG

REDIS_POOL = redis.ConnectionPool(host=CONFIG.REDIS['HOST'],
                                  port=CONFIG.REDIS['PORT'])

def connect_db(db_config):
    '''
    connect to the database
    '''
    connection = pymysql.connect(host=db_config['HOST'],
                                 port=db_config['PORT'],
                                 user=db_config['USER'],
                                 password=db_config['PASSWORD'],
                                 db=db_config['DB'],
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    logging.info('connect to the database')
    return connection

def get_db():
    '''
    get database connection, create if not exist
    '''
    if not hasattr(g, 'sql_db'):
        db_config = CONFIG.DB
        g.sql_db = connect_db(db_config)
    return g.sql_db

def next_id():
    '''
    generate primary id
    '''
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

@unique
class ResultCode(Enum):
    '''
    enum of result code
    '''
    Success = 0
    Invalid_Input = -1
    Repetitive_Record = -2
    Insert_Error = -3
    Update_Error = -4
    Delete_Error = -5

class Gender(object):
    '''
    enum of gender
    '''
    Male = '0'
    Female = '1'
    Unknown = '2'

class NotificationState(object):
    '''
    enum of notification state
    '''
    NotAllow = '0'
    Allow = '1'

class MerchantType(object):
    '''
    enum of merchant type
    '''
    Taobao = 'T'
    Tmall = 'TM'

class ItemState(object):
    '''
    enum of item state
    '''
    Valid = '00'
    Invalid = '01'

class ResponseBody(object):
    '''
    standard response struct
    '''
    __slots__ = ('result_code', 'msg', 'data')
    def __init__(self, result_code=ResultCode.Success, msg='成功', data=None):
        self.result_code = result_code
        self.msg = msg
        self.data = data

    def to_dict(self):
        '''
        convert to dict
        '''
        return {
            'result_code': self.result_code.value,
            'msg': self.msg,
            'data': self.data,
        }

class RedisKey(object):
    '''
    constants of redis key
    '''
    VALID_ITEMS = 'valid_items'
    UPDATED_ITEMS = 'updated_items'

class RedisItem(object):
    '''
    item structure for redis
    '''
    __slots__ = ('item_p_id', 'url', 'mall_type', 'name', 'image_url')
    def __init__(self, item_p_id, name, url, mall_type, image_url):
        self.item_p_id = item_p_id
        self.name = name
        self.url = url
        self.mall_type = mall_type
        self.image_url = image_url

    def redis_str(self):
        '''
        json str for redis store
        '''
        redis_item = dict()
        redis_item['id'] = self.item_p_id
        redis_item['url'] = self.url
        redis_item['mall_type'] = self.mall_type
        redis_item['name'] = self.name
        redis_item['image_url'] = self.image_url
        return json.dumps(redis_item, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
