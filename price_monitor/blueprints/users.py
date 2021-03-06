# -*- coding: utf-8 -*-

'''
user section
'''

import hashlib
import base64
from datetime import datetime
from flask import Blueprint, render_template, request, current_app, jsonify, session, redirect, url_for
from price_monitor.models import get_db, next_id, ResponseBody, ResultCode, Gender, NotificationState
from price_monitor.util.verify_util import verify_email, verify_password, verify_username
from price_monitor.util.encrypt_util import rsa_get_public_key, rsa_get_private_key, rsa_decrypt, gen_token

bp_users = Blueprint('users', __name__)
bp_users_api = Blueprint('users_api', __name__, url_prefix='/api')

def need_login(func):
    '''
    need login decorator
    '''
    def wrapper(*args, **kw):
        user = session.get('user', None)
        if not user:
            return redirect(url_for('users.login'))
        else:
            return func(*args, **kw)
    return wrapper

@bp_users.route('/user', methods=['GET'])
@need_login
def user_page():
    '''
    user page
    '''
    user = session.get('user', None)
    return render_template('user.html',
                           token=user['token'],
                           public_key=rsa_get_public_key().decode(),
                           notiState=user['notification_state'])

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
                (id, username, email, password, nickname, gender, notification_state, create_time)
                values (%s, %s, %s, %s, %s, %s, %s, %s)
                '''
        hash_password = username + email + origin_password
        md5 = hashlib.md5()
        md5.update(hash_password.encode('utf-8'))
        password = md5.hexdigest()
        cursor.execute(sql, (user_id, username, email, password,
                             username, Gender.Unknown, NotificationState.Allow, datetime.now()))
        if cursor.rowcount < 1:
            resp.result_code = ResultCode.Insert_Error
            resp.msg = '注册失败'
            return jsonify(resp.to_dict())
    connection.commit()
    token = gen_token(username)
    user = dict()
    user['user_id'] = user_id
    user['password'] = password
    user['nickname'] = username
    user['username'] = username
    user['email'] = email
    user['token'] = token
    user['image'] = None
    user['gender'] = Gender.Unknown
    user['notification_state'] = NotificationState.Allow

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
                    select id as user_id, username, email, password, nickname, image, gender, notification_state
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

@bp_users_api.route('/sign/password/update', methods=['POST'])
def api_update_password():
    '''
    change password api
    '''
    resp = ResponseBody()
    old_encode_password = base64.b64decode(request.json.get('oldPassword', ''))
    new_encode_password = base64.b64decode(request.json.get('newPassword', ''))
    private_key = rsa_get_private_key()
    old_password = rsa_decrypt(old_encode_password, private_key).decode()
    new_password = rsa_decrypt(new_encode_password, private_key).decode()
    error_msg = verify_password(new_password)
    # verify the new password
    if error_msg:
        resp.result_code = ResultCode.Invalid_Input
        resp.msg = error_msg
        return jsonify(resp.to_dict())

    user = session.get('user', None)
    user_id = user.get('user_id', '')
    username = user.get('username', '')
    email = user.get('email', '')
    password = user.get('password', '')

    old_hash_password = username + email + old_password
    md5 = hashlib.md5()
    md5.update(old_hash_password.encode('utf-8'))
    if password == md5.hexdigest():
        new_hash_password = username + email + new_password
        md5 = hashlib.md5()
        md5.update(new_hash_password.encode('utf-8'))
        new_hash_password = md5.hexdigest()

        connection = get_db()
        # update password
        with connection.cursor() as cursor:
            password_sql = 'update user set password = %s where id = %s'
            cursor.execute(password_sql, (new_hash_password, user_id))
            if cursor.rowcount < 1:
                resp.result_code = ResultCode.Update_Error
                resp.msg = '密码更新失败'
            else:
                connection.commit()
                user['password'] = new_hash_password
                session['user'] = user
                session.modified = True
    else:
        resp.result_code = ResultCode.Invalid_Input
        resp.msg = '旧密码错误'
    return jsonify(resp.to_dict())

@bp_users_api.route('/sign/notification_state/update', methods=['POST'])
def api_update_notification_state():
    '''
    update notification state api
    '''
    resp = ResponseBody()
    notification_state = request.json.get('notificationState', '')
    user = session.get('user', None)
    user_id = user.get('user_id', '')

    connection = get_db()
    with connection.cursor() as cursor:
        notification_state_sql = 'update user set notification_state = %s where id = %s'
        cursor.execute(notification_state_sql, (notification_state, user_id))
        if cursor.rowcount < 1:
            resp.result_code = ResultCode.Update_Error
            resp.msg = '推送设置更新失败'
        else:
            connection.commit()
            user['notification_state'] = notification_state
            session['user'] = user
            session.modified = True
    return jsonify(resp.to_dict())
