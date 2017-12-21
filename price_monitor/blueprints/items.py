# -*- coding: utf-8 -*-

'''
item section
'''

import logging
import json
from datetime import datetime
import redis
from flask import Blueprint, request, jsonify, session, render_template
from price_monitor.spider import taobao
from price_monitor.models import ResponseBody, ResultCode, get_db, next_id, ItemState, REDIS_POOL, RedisKey, RedisItem
from price_monitor.util.verify_util import contain_empty_str
from .errors import SQLError
from .users import need_login

bp_items = Blueprint('items', __name__)
bp_items_api = Blueprint('items_api', __name__, url_prefix='/api')

@bp_items.route('/')
@need_login
def index():
    '''
    index page
    '''
    user = session.get('user', None)
    return render_template('index.html', token=user['token'])

@bp_items_api.route('/sign/url/analysis', methods=['POST'])
def api_parse_url():
    '''
    parse the item url
    '''
    resp = ResponseBody()
    # varify the params
    url = request.json.get('url', '').strip()
    try:
        if url.find('tmall') > 0:
            tb_result = taobao.fetch_item_url(url, is_tmall=True)
            resp.data = tb_result
        elif url.find('taobao') > 0:
            tb_result = taobao.fetch_item_url(url, is_tmall=False)
            resp.data = tb_result
        else:
            resp.result_code = ResultCode.Invalid_Input
            resp.msg = '暂只支持淘宝或天猫链接'
            return jsonify(resp.to_dict())
    except Exception as error:
        resp.result_code = ResultCode.Invalid_Input
        resp.msg = getattr(error, 'message', '链接无效，或数据解析出错')

    return jsonify(resp.to_dict())

@bp_items_api.route('/sign/item/store', methods=['POST'])
def api_store_item():
    '''
    store the item info to database
    '''
    resp = ResponseBody()

    item_id = request.json.get('item_id', '').strip()
    url = request.json.get('url', '').strip()
    name = request.json.get('name', '').strip()
    image_url = request.json.get('image_url', '').strip()
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
        query_item_sql = 'select monitor_num from item where item_id=%s and mall_type=%s'
        cursor.execute(query_item_sql, (item_id, mall_type))
        items = cursor.fetchall()
        if not items:
            item_p_id = next_id()
            try:
                item_sql = '''
                           insert into item
                           (id, item_id, mall_type, url, name, image_url, shop_name, state, send_city, create_time, monitor_num)
                           values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
                           '''
                item_sql_params = (item_p_id, item_id, mall_type, url, name,
                                   image_url, shop_name, ItemState.Valid,
                                   send_city, nowtime)
                cursor.execute(item_sql, item_sql_params)
                if cursor.rowcount < 1:
                    raise SQLError(ResultCode.Insert_Error, item_sql, item_sql_params, '商品缓存失败')

                # store price record
                prices = request.json.get('prices', [])
                sku_groups = request.json.get('sku_groups', [])
                if not prices:
                    prices = []
                if not sku_groups:
                    sku_groups = []
                for info in prices:
                    item_price_sql = '''
                                     insert into item_price
                                     (id, item_p_id, name, pvs, price, stock, updated_time)
                                     values (%s, %s, %s, %s, %s, %s, %s)
                                     '''
                    info_name = info.get('names', '')
                    pvs = info.get('pvs', '')
                    stock = info.get('stock', '')
                    price = info.get('price', '')
                    item_price_sql_params = (next_id(), item_p_id, info_name,
                                             pvs, price, stock, nowtime)
                    cursor.execute(item_price_sql, item_price_sql_params)
                    if cursor.rowcount < 1:
                        raise SQLError(ResultCode.Insert_Error,
                                       item_price_sql,
                                       item_price_sql_params,
                                       '商品缓存失败')

                # store pvs record
                for group in sku_groups:
                    group_id = group.get('group_id', '').strip()
                    group_name = group.get('group_name', '').strip()
                    for sku in group.get('pvs', []):
                        sku_sql = '''
                                  insert into item_pvs
                                  (id, item_p_id, group_id, group_name, name, pvs)
                                  values (%s, %s, %s, %s, %s, %s)
                                  '''
                        pvs_name = sku.get('name', '')
                        sku_pvs = sku.get('pvs', '')
                        sku_sql_params = (next_id(), item_p_id, group_id,
                                          group_name, pvs_name, sku_pvs)
                        cursor.execute(sku_sql, sku_sql_params)
                        if cursor.rowcount < 1:
                            raise SQLError(ResultCode.Insert_Error,
                                           sku_sql,
                                           sku_sql_params,
                                           '商品缓存失败')
            except SQLError as error:
                resp.result_code = error.code
                resp.msg = error.message
                return jsonify(resp.to_dict())

            # cache to redis
            re_conn = redis.Redis(connection_pool=REDIS_POOL)
            redis_item_str = RedisItem(item_p_id, name, url, mall_type, image_url).redis_str()
            re_conn.sadd(RedisKey.VALID_ITEMS, redis_item_str)
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
            try:
                user_item_sql = '''
                                insert into user_item (user_id, item_p_id) values(%s, %s)
                                '''
                user_id = session['user']['user_id']
                user_item_params = (user_id, item_p_id)
                cursor.execute(user_item_sql, user_item_params)
                if cursor.rowcount < 1:
                    raise SQLError(ResultCode.Insert_Error, user_item_sql, user_item_params, '商品添加失败')

                if items:
                    item_monitor_sql = '''
                                       update item set monitor_num = %s where id = %s
                                       '''
                    item_monitor_params = (items[0]['monitor_num'] + 1, item_p_id)
                    cursor.execute(item_monitor_sql, item_monitor_params)
                    if cursor.rowcount < 1:
                        raise SQLError(ResultCode.Update_Error, item_monitor_sql, user_item_params, '商品添加失败')

            except SQLError as error:
                resp.result_code = error.code
                resp.msg = error.message
                return jsonify(resp.to_dict())
    connection.commit()

    return jsonify(resp.to_dict())

@bp_items_api.route('/sign/item/list', methods=['POST'])
def api_query_items():
    '''
    query registered items
    '''
    resp = ResponseBody()
    resp.data = query_items()
    return jsonify(resp.to_dict())

@bp_items_api.route('/sign/item/disconnection', methods=['POST'])
def api_disconnect_item():
    '''
    disconnect the item with user
    '''
    resp = ResponseBody()
    item_p_id = request.json.get('id', '').strip()
    user = session.get('user', None)
    connection = get_db()
    with connection.cursor() as cursor:
        try:
            delete_connection_sql = 'delete from user_item where user_id=%s and item_p_id=%s'
            delete_connection_params = (user['user_id'], item_p_id)
            cursor.execute(delete_connection_sql, delete_connection_params)
            if cursor.rowcount < 1:
                raise SQLError(ResultCode.Delete_Error,
                               delete_connection_sql,
                               delete_connection_params,
                               '商品删除失败')

            query_item_sql = 'select url, mall_type, name, monitor_num, image_url from item where id=%s'
            cursor.execute(query_item_sql, (item_p_id,))
            item = cursor.fetchall()[0]
            if item['monitor_num'] > 1:
                update_item_sql = 'update item set monitor_num = %s where id=%s'
                update_item_params = (item['monitor_num'] - 1, item_p_id)
                cursor.execute(update_item_sql, update_item_params)
            else:
                delete_item_sql = 'delete from item where id=%s'
                cursor.execute(delete_item_sql, (item_p_id,))

                delete_pvs_sql = 'delete from item_pvs where item_p_id=%s'
                cursor.execute(delete_pvs_sql, (item_p_id,))

                delete_price_sql = 'delete from item_price where item_p_id=%s'
                cursor.execute(delete_price_sql, (item_p_id,))

                # remove from redis
                re_conn = redis.Redis(connection_pool=REDIS_POOL)
                redis_item_str = RedisItem(item_p_id,
                                           item['name'],
                                           item['url'],
                                           item['mall_type'],
                                           item['image_url']).redis_str()
                re_conn.srem(RedisKey.VALID_ITEMS, redis_item_str)
        except SQLError as error:
            resp.result_code = error.code
            resp.msg = error.message
    connection.commit()
    return jsonify(resp.to_dict())

def query_items():
    '''
    query registered items
    '''
    user = session.get('user', None)
    connection = get_db()
    with connection.cursor() as cursor:
        query_item_sql = '''
                         select b.id, b.mall_type, b.item_id, b.name, b.url, b.image_url,
                         b.shop_name, b.send_city, b.state
                         from user_item a left outer join item b on a.item_p_id = b.id
                         where a.user_id = %s
                         '''
        cursor.execute(query_item_sql, (user['user_id'],))
        items = cursor.fetchall()
        if not items:
            return []
        for item in items:
            item_p_id = item['id']
            query_price_sql1 = "set @num := 0, @pvs := ''"
            cursor.execute(query_price_sql1, ())
            query_price_sql2 = '''
                                  select pvs, price, updated_time
                                  from (
                                  select pvs, price, updated_time, @num := if (@pvs = pvs, @num + 1, 1) as row_number, @pvs := pvs as dummy 
                                  from item_price
                                  where item_p_id = %s
                                  order by pvs asc, updated_time desc
                                  ) as x where x.row_number = 1
                                  '''
            cursor.execute(query_price_sql2, (item_p_id,))
            prices = cursor.fetchall()
            item['prices'] = prices

            item_pvs_group_list = []
            if len(prices) > 1:
                item_pvs_sql = 'select name, pvs, group_name from item_pvs where item_p_id = %s'
                cursor.execute(item_pvs_sql, (item_p_id,))
                item_pvs = cursor.fetchall()

                pvs_sample = prices[0]['pvs']
                for section in pvs_sample.split(';'):
                    group_id = section.split(':')[0]
                    pvs_sections = []
                    for pvs in item_pvs:
                        if pvs['pvs'].startswith(group_id):
                            pvs_sections.append(pvs)
                    item_pvs_group = dict()
                    item_pvs_group['group_id'] = group_id
                    item_pvs_group['group_name'] = pvs_sections[0]['group_name']
                    item_pvs_group['list'] = pvs_sections
                    item_pvs_group_list.append(item_pvs_group)
            item['item_pvs'] = item_pvs_group_list
        return items
