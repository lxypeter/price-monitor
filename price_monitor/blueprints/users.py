# -*- coding: utf-8 -*-

import logging
from flask import Blueprint, render_template, request, redirect, make_response

users = Blueprint('users', __name__)

@users.route('/')
def index():
    return render_template('index.html')

@users.route('/register', methods=['GET'])
def register():
    return render_template('register.html')

@users.route('/login')
def login():
    return render_template('login.html')

users_api = Blueprint('users_api', __name__, url_prefix='/api')

@users_api.before_request
def verify_sign():
    logging.info('======拦截')
    response = make_response()
    # return response

@users_api.route('/register', methods=['POST'])
def api_register():
    for key, value in request.json.items():
        logging.info(key + '======' + value)
    return ""
