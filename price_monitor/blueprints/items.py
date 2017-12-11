# -*- coding: utf-8 -*-

'''
item section
'''

import logging
from datetime import datetime
from price_monitor.spider import taobao
from flask import Blueprint, request, jsonify, session, redirect, render_template, url_for
from price_monitor.models import ResponseBody, ResultCode, get_db, next_id, ItemState
from price_monitor.util.verify_util import contain_empty_str
from .errors import InsertError

bp_items = Blueprint('items', __name__)
bp_items_api = Blueprint('items_api', __name__, url_prefix='/api')

@bp_items.route('/')
def index():
    '''
    index page
    '''
    user = session.get('user', None)
    if not user:
        return redirect(url_for('users.login'))
    return render_template('index.html', token=user['token'])

@bp_items_api.route('/sign/url/analysis', methods=['POST'])
def api_parse_url():
    '''
    parse the item url
    '''
    resp = ResponseBody()
    # varify the params
    url = request.json.get('url', '').strip()
    url_type = None
    if url.find('tmall') > 0:
        url_type = 'tmall'
    elif url.find('taobao') > 0:
        url_type = 'taobao'
    else:
        resp.result_code = ResultCode.Invalid_Input
        resp.msg = '暂只支持淘宝或天猫链接'
        return jsonify(resp.to_dict())

    try:
        tb_result = taobao.fetch_item_url(url, is_tmall=url_type)
    except Exception as error:
        resp.result_code = ResultCode.Invalid_Input
        resp.msg = getattr(error, 'message', '链接无效，或数据解析出错')

    resp.data = tb_result
    return jsonify(resp.to_dict())

@bp_items_api.route('/sign/item/store', methods=['POST'])
def api_store_item():
    '''
    store the item info to database
    '''
    resp = ResponseBody()

    item_id = request.json.get('item_id', '').strip()
    url = request.json.get('url', '').strip()
    name = request.json.get('item_name', '').strip()
    image_url = request.json.get('item_image', '').strip()
    shop_name = request.json.get('shop_name', '').strip()
    mall_type = request.json.get('mall_type', '').strip()
    send_city = request.json.get('send_city', '').strip()
    is_invalid = contain_empty_str([item_id, url, name, image_url, shop_name, mall_type, send_city])
    if is_invalid:
        resp.result_code = ResultCode.Invalid_Input
        resp.msg = '无效入参'
        return jsonify(resp.to_dict())

    # check whether the item has been stored
    nowtime = datetime.now()
    connection = get_db()
    with connection.cursor() as cursor:
        query_item_sql = 'select id from item where item_id=%s and mall_type=%s'
        cursor.execute(query_item_sql, (item_id, mall_type))
        values = cursor.fetchall()
        if not values:
            try:
                item_p_id = next_id()
                item_sql = '''
                        insert into item
                        (id, item_id, mall_type, url, name, image_url, shop_name, state, send_city, create_time)
                        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        '''
                item_sql_params = (item_p_id, item_id, mall_type, url, name,
                                   image_url, shop_name, ItemState.Valid.value,
                                   send_city, nowtime)
                cursor.execute(item_sql, item_sql_params)
                if cursor.rowcount < 1:
                    raise InsertError(item_sql, item_sql_params, '商品缓存失败')

                # store price record
                stock_info = request.json.get('stock_info', [])
                sku_groups = request.json.get('sku_groups', [])
                if not stock_info:
                    stock_info = []
                if not sku_groups:
                    sku_groups = []
                for info in stock_info:
                    item_price_sql = '''
                                    insert into item_price
                                    (id, item_p_id, name, pvs, stock, updated_time)
                                    values (%s, %s, %s, %s, %s, %s)
                                    '''
                    info_name = info.get('name', '')
                    pvs = info.get('pvs', '')
                    stock = info.get('stock', '')
                    item_price_sql_params = (next_id(), item_p_id, info_name,
                                             pvs, stock, nowtime)
                    cursor.execute(item_price_sql, item_price_sql_params)
                    if cursor.rowcount < 1:
                        raise InsertError(item_price_sql, item_price_sql_params, '商品缓存失败')

                # store pvs record
                for group in sku_groups:
                    group_id = group.get('group_id', '').strip()
                    for sku in group.get('pvs', []):
                        sku_sql = '''
                                insert into item_pvs
                                (id, item_p_id, group_id, name, pvs)
                                values (%s, %s, %s, %s, %s)
                                '''
                        pvs_name = sku.get('name', '')
                        sku_pvs = sku.get('pvs', '')
                        sku_sql_params = (next_id(), item_p_id, group_id, pvs_name, sku_pvs)
                        cursor.execute(sku_sql, sku_sql_params)
                        if cursor.rowcount < 1:
                            raise InsertError(sku_sql, sku_sql_params, '商品缓存失败')
            except InsertError as error:
                resp.result_code = ResultCode.Insert_Error.value
                resp.msg = error.message
                return jsonify(resp.to_dict())

        # check whether item has been connected with user
        query_user_sql = '''
                         select a.item_p_id from user_item a, item b
                         where a.item_p_id = b.id and b.item_id = %s and b.mall_type=%s
                         '''
        cursor.execute(query_user_sql, (item_id, mall_type))
        values = cursor.fetchall()
        if values:
            resp.msg = '商品已添加'
        else:
            user_item_sql = '''
                            insert into user_item (user_id, item_p_id) values(%s, %s)
                            '''
            user_id = session['user']['user_id']
            cursor.execute(user_item_sql, (user_id, item_p_id))
            if cursor.rowcount < 1:
                resp.result_code = ResultCode.Insert_Error.value
                resp.msg = '商品添加失败'
                return jsonify(resp.to_dict())
    connection.commit()

    return jsonify(resp.to_dict())

@bp_items_api.route('/sign/item/list', methods=['POST'])
def api_query_items():
    resp = ResponseBody()
    user = session.get('user', None)

    connection = get_db()
    with connection.cursor() as cursor:
        query_item_sql = '''
                         select b.id, b.mall_type, b.item_id, b.name, b.url, b.image_url
                         b.shop_name, b.send_city 
                         from user_item a left outer join item b on a.item_p_id = b.id
                         where a.user_id = %s
                         '''
        cursor.execute(query_item_sql, (user['user_id'],))
        items = cursor.fetchall()
        if not items:
            resp.data = []
            return jsonify(resp.to_dict())
        for item in items:
            item_p_id = item['id']
            query_price_sql = '''
                              select name, pvs, stock, updated_time from item_price
                              where item_p_id = %s
                              '''
            cursor.execute(query_price_sql, (item_p_id,))
            

        
    return jsonify(resp.to_dict())