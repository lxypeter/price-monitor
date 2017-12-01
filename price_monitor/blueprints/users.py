# -*- coding: utf-8 -*-

from flask import Blueprint, render_template

users = Blueprint('users', __name__)

@users.route('/')
def index():
    return render_template('index.html')

@users.route('/register')
def register():
    return render_template('register.html')

@users.route('/login')
def login():
    return render_template('login.html')
