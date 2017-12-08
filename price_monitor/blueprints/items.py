# -*- coding: utf-8 -*-

'''
item section
'''

import logging
from price_monitor.spider import taobao
from flask import Blueprint, request, jsonify
from price_monitor.models import ResponseBody, ResultCode

items_api = Blueprint('items_api', __name__, url_prefix='/api')

@items_api.route('/url_analysis', methods=['POST'])
def parse_url():
    '''
    parse the item url
    '''
    logging.info('进来了')
    resp = ResponseBody()
    # varify the params
    url = request.json.get('url', '').strip()
    url_type = None
    if url.find('tmall') > 0:
        url_type = 'tmall'
    elif url.find('taobao') > 0:
        url_type = 'taobao'
    else:
        resp.result_code = ResultCode.Invalid_Input.value
        resp.msg = '暂只支持淘宝或天猫链接'
        return jsonify(resp.to_dict())

    try:
        tb_result = taobao.fetch_item_url(url, is_tmall=url_type)
    except Exception as error:
        resp.result_code = ResultCode.Invalid_Input.value
        resp.msg = getattr(error, 'message', '链接无效，或数据解析出错')

    resp.data = tb_result
    return jsonify(resp.to_dict())
