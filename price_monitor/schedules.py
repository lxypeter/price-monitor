# -*- coding: utf-8 -*-

'''
server's schedule task
'''

__author__ = 'CY Lee'

import json
import redis
from price_monitor.spider import taobao
from .config import DefalutConfig
from .models import connect_db, RedisKey, MerchantType, REDIS_POOL

def update_item_info():
    '''
    update item info
    '''
    re_conn = redis.Redis(connection_pool=REDIS_POOL)
    valid_items = re_conn.smembers(RedisKey.VALID_ITEMS)

    connection = connect_db(DefalutConfig.DB)
    with connection.cursor() as cursor:
        for item_byte in valid_items:
            item = json.loads(item_byte.decode())
            new_item_info = None
            if item['mall_type'] == MerchantType.Tmall:
                new_item_info = taobao.fetch_item_url(item['url'], is_tmall=True)
            elif item['mall_type'] == MerchantType.Taobao:
                new_item_info = taobao.fetch_item_url(item['url'], is_tmall=False)

            old_item_prices_sql = '''
                                  set @num := 0, @pvs := '';
                                  select pvs, price, updated_time
                                  from (
                                  select pvs, price, updated_time, @num := if (@pvs = pvs, @num + 1, 1) as row_number, @pvs := pvs as dummy 
                                  from item_price
                                  where item_p_id = %s
                                  order by pvs asc, updated_time desc
                                  ) as x where x.row_number = 1
                                  '''
            cursor.execute(old_item_prices_sql, (item['id'],))
            old_item_prices = cursor.fetchall()
