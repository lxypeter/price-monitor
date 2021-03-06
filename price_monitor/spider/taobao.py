# -*- coding: utf-8 -*-

'''
淘宝爬虫
'''

__author__ = 'CY Lee'

import json
import re
from urllib import parse
import requests
from bs4 import BeautifulSoup
from price_monitor.models import MerchantType
from .errors import APIQueryError, ItemUrlError, InvalidItemError

_HEADER = {
    'authority':'detailskip.taobao.com',
    'method':'GET',
    'scheme':'https',
    'accept':'*/*',
    'accept-encoding':'gzip, deflate, br',
    'accept-language':'zh-CN,zh;q=0.9,en;q=0.8',
    'cookie':'l=Ant7DZw89YCtwTVC6H6fSNSxi1Xl0I/S; cna=PUPpEHOXtwICAQ6SJRx9Bfw1; t=a0e7b3e50bab0e4ea126d727ecf73a3b; cookie2=371cff6061e31957487ddee362fba529; v=0; _tb_token_=7a5519e8b35b; hng=CN%7Czh-CN%7CCNY%7C156; thw=cn; mt=ci%3D-1_1; isg=AkVFsOSHs8oZFJRI3yH0XOAhVId1L889CF3UOUer_Hzt3mVQDFIJZNN-njTT',
    'referer':'https://item.taobao.com/item.htm?spm=a230r.1.14.132.766fec1cYSS30p&id=558541926182&ns=1&abbucket=3',
    'user-agent':'''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36''',
}

_DETAIL_QRY_URL = 'https://detailskip.taobao.com/service/getData/1/p1/item/detail/sib.htm?modules=dynStock,qrcode,viewer,price,duty,xmpPromotion,delivery,activity,fqg,zjys,couponActivity,soldQuantity,originalPrice,tradeContract&itemId='

def fetch_item_url(url, **kw):
    '''
    爬取商品
    '''
    item = dict()
    item['url'] = url
    # 是否天猫
    is_tmall = kw.get('is_tmall', None)
    if is_tmall is None:
        if url.find('tmall') > 0:
            is_tmall = True
        else:
            is_tmall = False

    if is_tmall:
        item['mall_type'] = MerchantType.Tmall
    else:
        item['mall_type'] = MerchantType.Taobao

    # 解析url参数
    parse_result = parse.urlparse(url)
    url_params = parse.parse_qs(parse_result.query)
    try:
        item_id = url_params.get('id', [None])[0]
        item['item_id'] = item_id
    except IndexError:
        raise ItemUrlError(url=url, message='url格式不正确，缺失商品id')

    # 解析商品网页
    item_resp = requests.get(url, headers=_HEADER)
    item_soup = BeautifulSoup(item_resp.text, 'lxml')

    # 商品名
    item['name'] = get_item_name(item_soup)
    if item['name'] is None:
        if not verify_validity(item_soup):
            raise InvalidItemError(url, '商品无效或已下架', item_resp.text)

    # 商品图片
    item['image_url'] = get_item_image_url(item_soup)

    # 店铺名
    item['shop_name'] = get_item_shop_name(item_soup, url=url)

    # 价格
    item['price'] = get_item_def_price(item_soup)

    # sku tag
    (sku_dict, sku_groups) = get_item_sku(item_soup)
    item['sku_dict'] = sku_dict
    item['sku_groups'] = sku_groups

    # 查询商品详情
    detail_qry_url = _DETAIL_QRY_URL + item_id
    detail_resp = requests.get(detail_qry_url, headers=_HEADER)
    detail_dict = json.loads(detail_resp.text)
    detail_result_code = detail_dict.get('code').get('code', -1)
    try:
        if detail_result_code != 0:
            raise APIQueryError(detail_qry_url,
                                '淘宝商品详情查询失败 - item_id = ' + item_id,
                                detail_resp.text)
        # 发货地
        item['send_city'] = get_item_send_city(detail_dict)

        # 价格及库存
        item['prices'] = get_item_prices(item_soup, detail_dict, sku_dict, is_tmall)
    except APIQueryError as error:
        raise error
    except Exception as error:
        raise APIQueryError(detail_qry_url,
                            '淘宝商品详情查询失败 - body = ' + detail_resp.text,
                            detail_resp.text)
    return item

def get_item_name(item_soup):
    '''
    获取商品名称
    '''
    item_name = None
    item_name_tags = item_soup.find_all(['h1', 'h3'])
    for tag in item_name_tags:
        if tag.has_attr('data-spm') or ('tb-main-title' in tag.get('class', [])):
            item_name = ' '.join(tag.stripped_strings)
    return item_name

def get_item_image_url(item_soup):
    '''
    获取商品图片
    '''
    image_url = None
    item_image_tag = item_soup.find('img', id='J_ImgBooth')
    if not item_image_tag is None:
        item_image = item_image_tag.get('src', '')
        item_image = re.match(r'(/*)(.*)', item_image).groups()[1]
        image_url = u'http://' + item_image
    return image_url

def get_item_shop_name(item_soup, **kw):
    '''
    获取店铺名称
    '''
    shop_name = None
    shop_name_tag = item_soup.find(['a', 'div'],
                                   class_=re.compile(r'slogo-shopname|shop-name-link|tb-shop-name'))
    if shop_name_tag:
        shop_name = ''.join(shop_name_tag.stripped_strings)
    if kw['url'].find('chaoshi') > 0 and kw['url'].find('tmall') > 0:
        shop_name = '天猫超市'
    return shop_name

def get_item_def_price(item_soup):
    '''
    获取默认显示价格
    '''
    price = '0.00'
    price_tag = item_soup.find(['em', 'span'], class_=re.compile(r'tb-rmb-num|tm-price'))
    if price_tag:
        price = price_tag.string
    return price

def get_item_sku(item_soup):
    '''
    获取商品规格组
    '''
    sku_tags = item_soup.find_all('dl', class_=re.compile(r'(J_Prop tb-prop tb-clear|tb-prop tm-sale-prop tm-clear)(.*)'))
    sku_dict = None
    sku_groups = None
    if sku_tags:
        sku_dict = {}
        sku_groups = []
        for tag in sku_tags:
            sku_group = {}
            group_name = tag.find('dt').text
            sku_group['group_name'] = group_name
            sku_pvs = []

            ul_tag = tag.find('ul', class_=re.compile(r'(J_TSaleProp|tm-clear)(.*)'))
            li_tags = ul_tag.find_all('li')
            for index, li_tag in enumerate(li_tags):
                pvs = li_tag.get('data-value', '')
                if index == 0:
                    sku_group['group_id'] = pvs.split(':')[0]
                sku_pv = {}
                sku_pv['name'] = li_tag.find('span').text.strip()
                sku_pv['pvs'] = pvs
                sku_pvs.append(sku_pv)
                sku_dict[li_tag.get('data-value', '')] = li_tag.find('span').text.strip()
            sku_group['pvs'] = sku_pvs
            sku_groups.append(sku_group)
    return sku_dict, sku_groups

def get_item_send_city(detail_dict):
    '''
    获取发货地
    '''
    send_city = detail_dict.get('data').get('deliveryFee').get('data').get('sendCity')
    return send_city

def get_item_prices(item_soup, detail_dict, sku_dict, is_tmall):
    '''
    获取商品不同规格下价格
    '''
    prices = None
    if is_tmall and sku_dict:
        '''
        天猫
        '''
        sku_script = item_soup.find('script', text=re.compile(r'TShop.Setup'))
        sku_str = re.sub(r'\r|\n|\t', '', sku_script.text)
        sku_json_str = re.search(r'(TShop.Setup\()(.*)(\);}\)\(\);)', sku_str)[2]
        sku_json = json.loads(sku_json_str)
        sku_list = sku_json.get('valItemInfo').get('skuList')
        sku_map = sku_json.get('valItemInfo').get('skuMap')
        for sku_info in sku_list:
            key = ';' + sku_info['pvs'] + ';'
            sku_info.update(sku_map.get(key, {}))
        prices = sku_list
    else:
        '''
        普通商家
        '''
        prices = []
        price_dict = detail_dict.get('data').get('originalPrice')
        stock_dict = detail_dict.get('data').get('dynStock', {}).get('sku', {})
        for key, value in price_dict.items():
            sku_desc = []
            sku_info = {}
            sku_info['price'] = value.get('price', '0.00')
            if key == 'def':
                sku_info['pvs'] = 'def'
                sku_info['sellableQuantity'] = detail_dict.get('data').get('dynStock', {}).get('sellableQuantity', '0')
                sku_info['stock'] = detail_dict.get('data').get('dynStock', {}).get('stock', '0')
            else:
                sku_pvs = key.strip(';')
                sku_info['pvs'] = sku_pvs
                sku_keys = sku_pvs.split(';')
                for sku_key in sku_keys:
                    sku_desc.append(sku_dict.get(sku_key, ''))
                sku_info['names'] = ' '.join(sku_desc)

            sku_info.update(stock_dict.get(key, {}))
            prices.append(sku_info)

    # 促销价
    pmt_data = detail_dict.get('data').get('promotion').get('promoData')
    for key, value in pmt_data.items():
        for info in prices:
            if key == info.get('pvs', '') and value[0].get('price', None) != None:
                info['price'] = value[0].get('price', None)
    return prices

def verify_validity(item_soup):
    '''
    验证商品有效性
    '''
    error_tags = item_soup.find('div', class_=re.compile(r'errorDetail|error-notice-text'))
    error_content = error_tags.get_text()
    if re.search(r'找不到|下架|不存在', error_content):
        return False
    return True

# test_url = 'https://item.taobao.com/item.htm?spm=a230r.1.14.132.766fec1cYSS30p&id=558541926182&ns=1&abbucket=3#detail'
# test_url = 'https://detail.tmall.com/item.htm?spm=a230r.1.14.8.3dcf775f9YLkrD&id=555423143452&cm_id=140105335569ed55e27b&abbucket=3'
# test_url = 'http://chaoshi.detail.tmall.com/item.htm?id=36706363974&spm=875.7931836/B.2017039.7.56603756QDz44P&scm=1007.12144.81309.73136_0&pvid=fa5eb542-748f-47be-842c-79e96f3a42c0'
# test_url = 'https://detail.tmall.com/item.htm?spm=a1z10.1-b.w5003-16372475734.1.4461531fHczQQX&id=560284406679&rn=664265da2479d785617d97f27f227ae2&abbucket=12&scene=taobao_shop'
# test_url = 'https://item.taobao.com/item.htm?spm=a230r.1.14.38.3dcf775f9YLkrD&id=43690278010&ns=1&abbucket=3#detail'
# test_url = 'https://item.taobao.com/item.htm?spm=a230r.1.14.107.3dcf775f9YLkrD&id=544474625081&ns=1&abbucket=3#detail'
# test_url = 'https://detail.tmall.com/item.htm?id=546189339460&ali_refid=a3_430582_1006:1123721609:N:%E5%B0%BC%E5%B0%94:086cbe8fe056fd87eb1d73caa00105c1&ali_trackid=1_086cbe8fe056fd87eb1d73caa00105c1&spm=a230r.1.14.1&skuId=3507303059596'
# test_url = 'https://item.taobao.com/item.htm?spm=a230r.1.14.150.3747589cIany9R&id=546115767223&ns=1&abbucket=3#detail'
# fetch_item_url(test_url)
