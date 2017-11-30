# -*- coding: utf-8 -*-

from flask import Blueprint

users = Blueprint('users', __name__)

@users.route('/')
def login():
    return 'Hello'
