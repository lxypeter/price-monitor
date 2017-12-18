# -*- coding: utf-8 -*-

'''
user section
'''

import os
import hashlib
import base64
from datetime import datetime
from flask import Blueprint, render_template, request, current_app, jsonify, session, redirect, url_for
from price_monitor.models import get_db, next_id, ResponseBody, ResultCode, Gender
from price_monitor.util.verify_util import verify_email, verify_password, verify_username
from price_monitor.util.encrypt_util import rsa_get_public_key, rsa_get_private_key, rsa_decrypt, gen_token

bp_users = Blueprint('users', __name__)
bp_users_api = Blueprint('users_api', __name__, url_prefix='/api')

@bp_users.route('/user', methods=['GET'])
def user_page():
    '''
    user page
    '''
    user = session.get('user', None)
    if not user:
        return redirect(url_for('users.login'))
    return render_template('user.html')

@bp_users.route('/register', methods=['GET'])
def register():
    '''
    register page
    '''
    return render_template('register.html',
                           token=current_app.config['UNLOGINED_TOKEN'],
                           public_key=rsa_get_public_key().decode())

@bp_users.route('/login', methods=['GET'])
def login():
    '''
    login page
    '''
    return render_template('login.html',
                           token=current_app.config['UNLOGINED_TOKEN'],
                           public_key=rsa_get_public_key().decode())

@bp_users.route('/logout')
def logout():
    '''
    logout and redirect to index
    '''
    session.pop('user', None)
    return redirect(url_for('users.login'))

@bp_users_api.route('/register', methods=['POST'])
def api_register():
    '''
    register api
    '''
    resp = ResponseBody()
    # varify the params
    username = request.json.get('username', '').strip()
    encrypt_password = base64.b64decode(request.json.get('password', ''))
    email = request.json.get('email', '').strip()
    private_key = rsa_get_private_key()
    origin_password = rsa_decrypt(encrypt_password, private_key).decode()
    error_msg = verify_username(username) or verify_password(origin_password) or verify_email(email)
    if error_msg:
        resp.result_code = ResultCode.Invalid_Input
        resp.msg = error_msg
        return jsonify(resp.to_dict())

    connection = get_db()
    user_id = next_id()
    # check if username or email exist
    with connection.cursor() as cursor:
        query_sql = 'select id, username, email from user where username=%s or email=%s'
        cursor.execute(query_sql, (username, email))
        values = cursor.fetchall()
        if values:
            resp.result_code = ResultCode.Repetitive_Record
            if values[0].get('username', '') == username:
                resp.msg = '用户名%s已注册' % username
            elif values[0].get('email', '') == email:
                resp.msg = '邮箱%s已注册' % email
            return jsonify(resp.to_dict())

        # insert the record
        sql = '''
                insert into user
                (id, username, email, password, nickname, gender, create_time)
                values (%s, %s, %s, %s, %s, %s, %s)
                '''
        hash_password = username + email + origin_password
        md5 = hashlib.md5()
        md5.update(hash_password.encode('utf-8'))
        password = md5.hexdigest()
        cursor.execute(sql, (user_id, username, email, password,
                             username, Gender.Unknown.value, datetime.now()))
        if cursor.rowcount < 1:
            resp.result_code = ResultCode.Insert_Error
            resp.msg = '注册失败'
            return jsonify(resp.to_dict())
    connection.commit()
    token = gen_token(username)
    user = dict()
    user['user_id'] = user_id
    user['nickname'] = username
    user['username'] = username
    user['email'] = email
    user['token'] = token
    user['image'] = None
    user['gender'] = Gender.Unknown.value

    session['user'] = user
    return jsonify(resp.to_dict())

@bp_users_api.route('/login', methods=['POST'])
def api_login():
    '''
    login api
    '''
    resp = ResponseBody()
    account = request.json.get('account', '').strip()
    encrypt_password = base64.b64decode(request.json.get('password', ''))
    private_key = rsa_get_private_key()
    origin_password = rsa_decrypt(encrypt_password, private_key).decode()

    connection = get_db()
    # query user
    with connection.cursor() as cursor:
        query_sql = '''
                    select id as user_id, username, email, password, nickname, image, gender
                    from user where username=%s or email=%s
                    '''
        cursor.execute(query_sql, (account, account))
        values = cursor.fetchall()
        if values:
            user = values[0]
            username = user.get('username', '')
            email = user.get('email', '')
            password = user.get('password', '')

            hash_password = username + email + origin_password
            md5 = hashlib.md5()
            md5.update(hash_password.encode('utf-8'))
            if password == md5.hexdigest():
                token = gen_token(username)
                user['token'] = token
                session['user'] = user
            else:
                resp.result_code = ResultCode.Invalid_Input
                resp.msg = '密码错误'
        else:
            resp.result_code = ResultCode.Invalid_Input
            resp.msg = '用户名或邮箱不存在'
    return jsonify(resp.to_dict())
