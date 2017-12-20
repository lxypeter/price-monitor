# -*- coding: utf-8 -*-

'''
server's schedule task
'''

__author__ = 'CY Lee'

import json
from datetime import datetime
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib
import redis
from price_monitor.spider import taobao, errors
from .config import DefalutConfig
from .models import connect_db, RedisKey, MerchantType, REDIS_POOL, next_id, ItemState

def update_item_info():
    '''
    update item info, if price has changed, insert new record into db
    '''
    # get item list from redis
    re_conn = redis.Redis(connection_pool=REDIS_POOL)
    valid_items = re_conn.smembers(RedisKey.VALID_ITEMS)

    connection = connect_db(DefalutConfig.DB)
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

def send_reminder_emails():
    # 不能简单地传入name <addr@example.com>，因为如果包含中文，需要通过Header对象进行编码
    def _format_addr(s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))
    # 输入Email地址和口令:
    from_addr = input('From: ')
    password = input('Password: ')
    # 输入收件人地址:
    to_addr = input('To: ')
    # 输入SMTP服务器地址:
    smtp_server = input('SMTP server: ')

    # &0就是邮件正文，&1是MIME的subtype，传入'plain'表示纯文本
    msg = MIMEText('hello, send by Python...', 'plain', 'utf-8')
    msg['From'] = _format_addr('Python爱好者 <%s>' % from_addr)
    # 是字符串而不是list，如果有多个邮件地址，用,分隔即可
    msg['To'] = _format_addr('管理员 <%s>' % to_addr)
    msg['Subject'] = Header('来自SMTP的问候……', 'utf-8').encode()

    server = smtplib.SMTP(DefalutConfig.EMAIL_SERVER['HOST'], DefalutConfig.EMAIL_SERVER['PORT'])

    server.set_debuglevel(1) # 打印出和SMTP服务器交互的所有信息
    server.login(from_addr, password) 
    server.sendmail(from_addr, [to_addr], msg.as_string())
    server.quit()
