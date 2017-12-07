# -*- coding: utf-8 -*-

'''
encrypt and descrypt util
'''

import logging

from flask import current_app
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

def rsa_create_keys():
    '''
    generate keys (private key, public key)
    '''
    key = RSA.generate(1024)
    return key.exportKey(), key.publickey().exportKey()

def rsa_get_public_key():
    '''
    get rsa public key from app.config
    '''
    return current_app.config['RSA_PUBLIC_KEY']

def rsa_get_private_key():
    '''
    get rsa private key from app.config
    '''
    return current_app.config['RSA_PRIVATE_KEY']

def rsa_decrypt(origin_str, key):
    '''
    key: public key in bytes
    '''
    private_key = RSA.import_key(key)
    cipher_rsa_decrypt = PKCS1_v1_5.new(private_key)
    message = cipher_rsa_decrypt.decrypt(origin_str, b'')
    return message
