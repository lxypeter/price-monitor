# -*- coding: utf-8 -*-

'''
create the application
'''

__author__ = 'CY Lee'

import logging
from io import StringIO
import hashlib
from datetime import datetime
from flask import Flask, g, request, make_response
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

    app.jinja_env.variable_start_string = '{['
    app.jinja_env.variable_end_string = ']}'

    # register blueprint
    app.register_blueprint(users)

    # register request filter
    @app.before_request
    def url_filter():
        '''
        request filter handler
        '''
        if request.path.startswith('/api'):
            return verify_sign(app)

    # init database
    register_teardowns(app)

    logging.info('server started')
    return app

def register_teardowns(app):
    '''
    close database connection when server teardown
    '''
    @app.teardown_appcontext
    def close_db(error):
        '''
        close database connection
        '''
        if hasattr(g, 'sql_db'):
            g.sql_db.close()

def verify_sign(app):
    '''
    verifty the api sign
    '''
    date_str = request.headers['date-str']
    # valid request in 60s
    header_ts = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').timestamp()
    current_ts = datetime.now().timestamp()
    if abs(header_ts - current_ts) > 60:
        return make_response(('Overtime Request', 500))
    # verify sign
    keys = list(dict(request.json).keys())
    keys.sort()
    str_io = StringIO()
    token = app.config['UNLOGINED_TOKEN']
    if request.path.startswith('/api/sign'):
        token = app.config['LOGINED_TOKEN']
    str_io.write(token)
    for key in keys:
        str_io.write(key)
        str_io.write(request.json.get(key))
    str_io.write(date_str)
    sha1 = hashlib.sha1()
    sha1.update(str_io.getvalue().encode('utf-8'))
    sign = sha1.hexdigest().upper()
    header_sign = request.headers['sign']
    if sign != header_sign:
        return make_response(('Invalid Sign', 500))
