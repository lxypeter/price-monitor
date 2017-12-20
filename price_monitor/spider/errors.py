# -*- coding: utf-8 -*-

'''
爬虫通用Exception
'''

__author__ = 'CY Lee'

class ItemUrlError(Exception):
    '''
    商品链接错误
    '''
    def __init__(self, url='', message=''):
        super(ItemUrlError, self).__init__(message)
        self.url = url
        self.message = message

class APIQueryError(Exception):
    '''
    接口访问错误
    '''
    def __init__(self, url='', message='', body=''):
        super(APIQueryError, self).__init__(message)
        self.url = url
        self.message = message
        self.body = body

class InvalidItemError(Exception):
    '''
    商品无效或下架
    '''
    def __init__(self, url='', message='', body=''):
        super(InvalidItemError, self).__init__(message)
        self.url = url
        self.message = message
        self.body = body
