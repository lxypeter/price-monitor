# -*- coding: utf-8 -*-

'''
create the application
'''

__author__ = 'CY Lee'

import logging
from flask import Flask, g
from .blueprints.users import users

def create_app():
    '''
    create the application
    '''
    logging.basicConfig(level=logging.INFO)
    # init app and load configuration
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config')
    app.config.from_pyfile('config.py')
    # register blueprint
    app.register_blueprint(users)
    # init database
    register_teardowns(app)

    logging.info('server started')
    return app

def register_teardowns(app):
    '''
    close database connection when server teardown
    '''
    @app.teardown_appcontext
    def close_db():
        '''
        close database connection
        '''
        if hasattr(g, 'sql_db'):
            g.sql_db.close()
