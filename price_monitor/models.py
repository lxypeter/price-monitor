# -*- coding: utf-8 -*-

'''
application's models and database method
'''

__author__ = 'CY Lee'

import logging
import time
import uuid
from flask import current_app, g
import pymysql.cursors

def connect_db():
    '''
    connect to the database
    '''
    connection = pymysql.connect(host=current_app.config['HOST'],
                                 port=current_app.config['PORT'],
                                 user=current_app.config['USER'],
                                 password=current_app.config['PASSWORD'],
                                 db=current_app.config['DB'],
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
