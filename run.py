# -*- coding: utf-8 -*-

'''
run the server
'''

__author__ = 'CY Lee'

from price_monitor.factory import create_app
# from price_monitor.models import get_db

if __name__ == '__main__':
    APP = create_app()
    APP.run()
