# -*- coding: utf-8 -*-

'''
form input verify util
'''

import re

def verify_username(username):
    '''
    verify username
    '''
    if not re.match(r'^[0-9a-zA-Z\_]{6,16}$', username):
        return '用户名需由6-16位数字、字母或下划线组成'

def verify_password(password):
    '''
    verify password
    '''
    if not re.match(r'^[0-9a-zA-Z\_]{6,16}$', password):
        return '密码需由6-16位数字、字母或下划线组成'

def verify_email(email):
    '''
    verify email
    '''
    if not re.match(r'^[a-z_0-9.-]{1,64}@([a-z0-9-]{1,200}.){1,5}[a-z]{1,6}$', email):
        return '请输入有效的电子邮箱'
