# -*- coding: utf-8 -*-

'''
run the server
'''

__author__ = 'CY Lee'

from price_monitor.factory import create_app

if __name__ == '__main__':
    APP = create_app()
    APP.run(use_reloader=False)
