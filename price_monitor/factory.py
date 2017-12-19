# -*- coding: utf-8 -*-

'''
create the application
'''

__author__ = 'CY Lee'

import logging
from io import StringIO
import hashlib
from datetime import datetime
import json
import functools
import redis
from flask import Flask, g, request, make_response, session
from apscheduler.schedulers.background import BackgroundScheduler
from .models import connect_db, RedisKey, REDIS_POOL
from .blueprints.users import bp_users, bp_users_api
from .blueprints.items import bp_items, bp_items_api
from .util.encrypt_util import rsa_create_keys
from .config import DefalutConfig
from .schedules import update_item_info

def create_app():
    '''
    create the application
    '''
    logging.basicConfig(level=logging.INFO)
    # init app and load configuration
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(DefalutConfig)
    app.config.from_pyfile('config.py')
    keys = rsa_create_keys()
    app.config.update({
        'RSA_PUBLIC_KEY': keys[1],
        'RSA_PRIVATE_KEY': keys[0],
    })

    app.jinja_env.variable_start_string = '{['
    app.jinja_env.variable_end_string = ']}'

    # register blueprint
    register_blueprints(app)

    # register app lifetime events
    register_app_lifetime_events(app)

    # register redis
    register_redis()

    # register scheduler
    register_scheduler()

    logging.info('server started')
    return app

def register_blueprints(app):
    '''
    register blueprints
    '''
    app.register_blueprint(bp_users)
    app.register_blueprint(bp_users_api)
    app.register_blueprint(bp_items)
    app.register_blueprint(bp_items_api)

def register_app_lifetime_events(app):
    '''
    register app lifetime events
    '''
    @app.before_request
    def before_request():
        '''
        url filter
        '''
        if request.path.startswith('/api'):
            return verify_sign(app)

    @app.context_processor
    def inject_user():
        '''
        add user info from session
        '''
        return dict(user=session.get('user', None))

    @app.teardown_appcontext
    def teardown(error):
        '''
        close database connection and scheduler
        '''
        # close database connection
        if hasattr(g, 'sql_db'):
            logging.info('close the database connection')
            g.sql_db.close()

def register_redis():
    '''
    init redis
    '''
    # cache valid items
    connection = connect_db(DefalutConfig.DB)
    with connection.cursor() as cursor:
        valid_items_sql = 'select id, url, mall_type, name from item where monitor_num > 0'
        cursor.execute(valid_items_sql, ())
        valid_items = cursor.fetchall()
        re_pipe = redis.Redis(connection_pool=REDIS_POOL).pipeline(transaction=True)
        re_pipe.delete(RedisKey.VALID_ITEMS)
        for item in valid_items:
            item_json = json.dumps(item, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
            re_pipe.sadd(RedisKey.VALID_ITEMS, item_json)
        re_pipe.execute()

def register_scheduler():
    '''
    register scheduler
    '''
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_item_info, 'interval', minutes=30)
    scheduler.start()

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
        token = session['user']['token']
    str_io.write(token)
    for key in keys:
        str_io.write(key)
        value = request.json.get(key, '')
        if value is None:
            value = ''
        value = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        str_io.write(value)
    str_io.write(date_str)
    sha1 = hashlib.sha1()
    sha1.update(str_io.getvalue().encode('utf-8'))
    sign = sha1.hexdigest().upper()
    header_sign = request.headers['sign']
    if sign != header_sign:
        logging.error('invalid sign')
        logging.info(header_sign)
        return make_response(('Invalid Sign', 500))
