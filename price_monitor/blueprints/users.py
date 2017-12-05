# -*- coding: utf-8 -*-

import logging
from flask import Blueprint, render_template, request, redirect, make_response, current_app
from price_monitor.models import get_db, next_id

users = Blueprint('users', __name__)

@users.route('/')
def index():
    return render_template('index.html')

@users.route('/register', methods=['GET'])
def register():
    logging.info('token======' + current_app.config['UNLOGINED_TOKEN'])
    return render_template('register.html', token=current_app.config['UNLOGINED_TOKEN'])

@users.route('/login')
def login():
    return render_template('login.html')

@users.route('/api/register', methods=['POST']) 
def api_register():
    # varify the params

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
