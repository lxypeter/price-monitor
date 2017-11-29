# -*- coding: utf-8 -*-

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
