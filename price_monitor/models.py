# -*- coding: utf-8 -*-

'''
application's models and database method
'''

__author__ = 'CY Lee'

import logging
import time
import uuid
from enum import Enum, unique
from flask import current_app, g
import pymysql.cursors

def connect_db():
    '''
    connect to the database
    '''
    db_config = current_app.config['DB']
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
        g.sql_db = connect_db()
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

@unique
class Gender(Enum):
    '''
    enum of gender
    '''
    Male = 0
    Female = 1
    Unknown = 2

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
