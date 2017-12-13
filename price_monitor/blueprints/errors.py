# -*- coding: utf-8 -*-

'''
BluePrint通用Exception
'''

__author__ = 'CY Lee'

class SQLError(Exception):
    '''
    数据库Insert失败
    '''
    def __init__(self, code=0, sql='', params=None, message=''):
        super(SQLError, self).__init__(message)
        self.code = code
        self.sql = sql
        self.params = params
        self.message = message
