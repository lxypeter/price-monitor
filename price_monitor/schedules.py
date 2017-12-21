# -*- coding: utf-8 -*-

'''
server's schedule task
'''

__author__ = 'CY Lee'

import os
import json
from datetime import datetime
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib
import redis
from jinja2 import Environment, FileSystemLoader
from price_monitor.spider import taobao, errors
from config.config import CONFIG
from .models import connect_db, RedisKey, MerchantType, REDIS_POOL, next_id, ItemState

def update_item_info():
    '''
    update item info, if price has changed, insert new record into db
    '''
    # get item list from redis
    re_conn = redis.Redis(connection_pool=REDIS_POOL)
    valid_items = re_conn.smembers(RedisKey.VALID_ITEMS)

    connection = connect_db(CONFIG.DB)
    for item_byte in valid_items:
        item_json_str = item_byte.decode()
        item = json.loads(item_json_str)
        nowtime = datetime.now()
        new_item_info = None
        # fetch new item info
        try:
            if item['mall_type'] == MerchantType.Tmall:
                new_item_info = taobao.fetch_item_url(item['url'], is_tmall=True)
            elif item['mall_type'] == MerchantType.Taobao:
                new_item_info = taobao.fetch_item_url(item['url'], is_tmall=False)
        except errors.InvalidItemError:
            with connection.cursor() as cursor:
                invalid_item_sql = 'update item set state = %s where id = %s'
                cursor.execute(invalid_item_sql, (ItemState.Invalid, item['id']))
            connection.commit()
            # remove item from redis
            re_conn.srem(RedisKey.VALID_ITEMS, item_json_str)
            continue

        with connection.cursor() as cursor:
            old_item_prices_sql1 = "set @num := 0, @pvs := ''"
            cursor.execute(old_item_prices_sql1, ())
            old_item_prices_sql2 = '''
                                    select pvs, price, updated_time
                                    from (
                                    select pvs, price, updated_time, @num := if (@pvs = pvs, @num + 1, 1) as row_number, @pvs := pvs as dummy 
                                    from item_price
                                    where item_p_id = %s
                                    order by pvs asc, updated_time desc
                                    ) as x where x.row_number = 1
                                    '''
            cursor.execute(old_item_prices_sql2, (item['id'],))
            old_item_prices = cursor.fetchall()
            # convert the result to dict, for further search
            old_price_dict = dict()
            for old_price in old_item_prices:
                old_price_dict[old_price['pvs']] = old_price

            updated_item = None
            # compare new prices to old prices. if there is any different, insert the new record
            for new_price in new_item_info['prices']:
                old_price = old_price_dict.get(new_price['pvs'], None)
                if not old_price or new_price['price'] != old_price['price']:
                    new_price_sql = '''
                                    insert into item_price
                                    (id, item_p_id, name, pvs, price, stock, updated_time)
                                    values (%s, %s, %s, %s, %s, %s, %s)
                                    '''
                    info_name = new_price.get('names', '')
                    pvs = new_price.get('pvs', '')
                    stock = new_price.get('stock', '')
                    price = new_price.get('price', '')
                    new_price_sql_params = (next_id(), item['id'], info_name,
                                            pvs, price, stock, nowtime)
                    cursor.execute(new_price_sql, new_price_sql_params)

                    if updated_item is None:
                        updated_item = dict()
                        updated_item['id'] = item['id']
                        updated_item['url'] = item['url']
                        updated_item['name'] = item['name']
                        updated_item['image_url'] = item['image_url']
                        updated_item['updated_time'] = nowtime.strftime('%Y-%m-%d %H:%M:%S')
                        updated_item['updated_prices'] = []
                    item_price_update = dict()
                    item_price_update['name'] = info_name
                    if old_price:
                        item_price_update['old_price'] = old_price['price']
                    else:
                        item_price_update['old_price'] = None
                    item_price_update['new_price'] = new_price['price']
                    updated_item['updated_prices'].append(item_price_update)
            # cache updated item in redis, for email reminder
            if updated_item:
                updated_item_json = json.dumps(updated_item,
                                                ensure_ascii=False,
                                                separators=(',', ':'),
                                                sort_keys=True)
                re_conn.sadd(RedisKey.UPDATED_ITEMS, updated_item_json)

            # compare pvs
            old_item_pvs_sql = 'select name, pvs from item_pvs where item_p_id = %s'
            cursor.execute(old_item_pvs_sql, (item['id'],))
            old_item_pvs = cursor.fetchall()
            new_sku_dict = new_item_info.get('sku_dict', {})
            if new_sku_dict is None:
                new_sku_dict = {}
            for key, value in new_sku_dict.items():
                has_pvs_exist = False
                for pvs in old_item_pvs:
                    if key == pvs['pvs']:
                        has_pvs_exist = True
                        break
                if not has_pvs_exist:
                    sku_sql = '''
                            insert into item_pvs
                            (id, item_p_id, group_id, name, pvs)
                            values (%s, %s, %s, %s, %s)
                            '''
                    pvs_name = value
                    sku_pvs = key
                    group_id = key.split(':')[0]
                    sku_sql_params = (next_id(), item['id'], group_id, pvs_name, sku_pvs)
                    cursor.execute(sku_sql, sku_sql_params)
            connection.commit()
    connection.close()

def send_reminder_emails():
    '''
    get updated item list and send email to user
    '''
    # get updated item list from redis
    re_conn = redis.Redis(connection_pool=REDIS_POOL)
    updated_items = re_conn.smembers(RedisKey.UPDATED_ITEMS)

    # email basic setting
    def _format_addr(email_str):
        '''
        convert email address from str like: nickname <email@address.com>
        '''
        name, addr = parseaddr(email_str)
        return formataddr((Header(name, 'utf-8').encode(), addr))
    server = smtplib.SMTP(CONFIG.EMAIL_SERVER['HOST'], CONFIG.EMAIL_SERVER['PORT'])
    server.set_debuglevel(1)
    account_addr = CONFIG.EMAIL_ACCOUNT['ADDR']
    server.login(account_addr, CONFIG.EMAIL_ACCOUNT['PASSWORD'])

    options = dict(variable_start_string='{[', variable_end_string=']}')
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    env = Environment(loader=FileSystemLoader(path), **options)

    connection = connect_db(CONFIG.DB)
    with connection.cursor() as cursor:
        for item_byte in updated_items:
            item_json_str = item_byte.decode()
            item = json.loads(item_json_str)

            monitor_users_sql = '''
                                select b.nickname, b.email
                                from user_item a left outer join user b on a.user_id = b.id
                                where a.item_p_id = %s
                                '''
            cursor.execute(monitor_users_sql, (item['id'],))
            users = cursor.fetchall()
            mail_body = env.get_template('email_body.html').render(item=item).encode('utf-8')
            
            for user in users:
                msg = MIMEText(mail_body, 'html', 'utf-8')
                msg['From'] = _format_addr('%s <%s>' % (CONFIG.EMAIL_ACCOUNT['NAME'], account_addr))
                msg['To'] = _format_addr('%s <%s>' % (user['nickname'], user['email']))
                msg['Subject'] = Header('等价：您关注的商品: %s 价格有所变动' % item['name'], 'utf-8').encode()
                server.sendmail(CONFIG.EMAIL_ACCOUNT['ADDR'], [user['email']], msg.as_string())
    server.quit()
    connection.close()
