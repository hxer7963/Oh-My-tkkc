# encoding=utf-8
"""
@author: hxer
@contact: hxer7963@gmail.com
@time: 2017/4/21 23:38
"""
import time
from math import floor
from requests import Session, exceptions
from random import randint

header = {
    'Accept': 'text/html,text/javascript,application/json,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Host': 'tkkc.hfut.edu.cn',
    'Origin': 'http://tkkc.hfut.edu.cn',
    'Referer': 'http://tkkc.hfut.edu.cn',
    'Upgrade-Insecure-Requests': '1',
    'Cookie': '',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/56.0.2924.87 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}


def date():
    return str(floor(time.time()*1000))

ROOT_URL = 'http://tkkc.hfut.edu.cn'
session = Session()
cookies = dict()

def updateHeader(URL): # (header, key):
    """merge the session.cookies dict to header Cookie,
    and update Referer to the URL which is request just now!"""
    cookies.update(session.cookies)
    header['Cookie'] = '; '.join([str(key)+'='+str(value) for key, value in session.cookies.items()])
    # print(header['Cookie'])
    header['Referer'] = URL


def request(*args):
    """GET/POST data from/to website, then return the response text if success"""
    URL = ROOT_URL + args[0]
    proxies = {'https': 'http://137.123.%s.135:8234' % randint(2, 233)}
    # print(args[0])
    if len(args) == 1:  # GET method
        response = session.get(URL, headers=header, proxies=proxies)
        updateHeader(URL)
    else:   # POST with data parameter addition
        response = session.post(URL, headers=header, data=args[1], proxies=proxies)
    try:
        response.raise_for_status()
    except UnboundLocalError as exc:
        print(exc)
        if len(args) == 2:
            print('POST FAIL! continue to file question')
        else:
            import traceback
            print(traceback.format_exc())
            exit(1)
    else:
        return response
