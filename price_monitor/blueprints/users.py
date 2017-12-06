# -*- coding: utf-8 -*-

'''
user section
'''

import logging
import base64
from flask import Blueprint, render_template, request, redirect, current_app, jsonify
from price_monitor.models import get_db, next_id, ResponseBody, ResultCode
from price_monitor.util.verify_util import verify_email, verify_password, verify_username
from price_monitor.util.encrypt_util import rsa_get_public_key, rsa_get_private_key, rsa_decrypt

users = Blueprint('users', __name__)

@users.route('/')
def index():
    '''
    index page
    '''
    return render_template('index.html')

@users.route('/register', methods=['GET'])
def register():
    '''
    register page
    '''
    return render_template('register.html',
                           token=current_app.config['UNLOGINED_TOKEN'],
                           public_key=rsa_get_public_key())

@users.route('/login')
def login():
    '''
    login page
    '''
    return render_template('login.html')

@users.route('/api/register', methods=['POST'])
def api_register():
    '''
    register api
    '''
    resp = ResponseBody()
    # varify the params
    username = request.json.get('username', '')
    encrypt_password = base64.b64decode(request.json.get('password', ''))
    email = request.json.get('email', '')
    private_key = rsa_get_private_key()
    origin_password = rsa_decrypt(encrypt_password, private_key).decode()

    error_msg = verify_username(username) or verify_password(origin_password) or verify_email(email)
    if error_msg:
        resp.result_code = ResultCode.Invalid_Input
        resp.msg = error_msg
        return jsonify(resp.to_dict())

    connection = get_db()
    # check if username or email exist


    # insert the record
    # `id` varchar(50) not null,
    # `username` varchar(50) not null,
    # `email` varchar(50) not null,
    # `password` varchar(50) not null,
    # `nickname` varchar(50) not null,
    # `gender` char(1) not null,
    # `image` varchar(500),
    # `create_time` real not null,
    try:
        with connection.cursor() as cursor:
            sql = '''
                  insert into user
                  (id, username, email, password, nickname, gender, create_time)
                  values (%s, %s, %s, %s, %s, %s, %s)
                  '''
            cursor.execute(sql, [next_id(), ])
        connection.commit()
    finally:
        connection.close()
    for key, value in request.json.items():
        logging.info(key + '======' + value)
    return ""
