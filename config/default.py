# -*- coding: utf-8 -*-

'''
default configuration
'''

__author__ = 'CY Lee'

class DefaultConfig(object):
    '''
    Default configurations.
    '''
    DEBUG = False
    SECRET_KEY = 'DEVELOPMENT_SECRET_KEY'
    DB = {
        'HOST': '127.0.0.1',
        'PORT': 3306,
        'USER': 'root',
        'PASSWORD': '123',
        'DB': 'price_monitor'
    }
    REDIS = {
        'HOST': '127.0.0.1',
        'PORT': 6379,
    }
    UNLOGINED_TOKEN = 'DEVELOPMENT_UNLOGINED_TOKEN'
    LOGINED_TOKEN = 'DEVELOPMENT_LOGINED_TOKEN'
    EMAIL_SERVER = {
        'HOST': 'smtp.sina.com',
        'PORT': 25,
    }
    EMAIL_ACCOUNT = {
        'NAME': '等价',
        'ADDR': 'example@sina.com',
        'PASSWORD': 'example',
    }
