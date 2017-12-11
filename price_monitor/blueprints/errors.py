# -*- coding: utf-8 -*-

'''
BluePrint通用Exception
'''

__author__ = 'CY Lee'

class InsertError(Exception):
    '''
    数据库Insert失败
    '''
    def __init__(self, sql='', params=None, message=''):
        super(InsertError, self).__init__(message)
        self.sql = sql
        self.params = params
        self.message = message
