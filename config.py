# -*- coding: utf-8 -*-

'''
Default configurations.
'''

__author__ = 'CY Lee'

DEBUG = False
SECRET_KEY = 'DEVELOPMENT_SECRET_KEY'
DB = {
    'HOST': '127.0.0.1',
    'PORT': 3306,
    'USER': 'root',
    'PASSWORD': '123',
    'DB': 'price_monitor'
}
UNLOGINED_TOKEN = 'DEVELOPMENT_UNLOGINED_TOKEN'
LOGINED_TOKEN = 'DEVELOPMENT_LOGINED_TOKEN'
