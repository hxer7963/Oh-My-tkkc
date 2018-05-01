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

from tkkc import header, BASE_URL


def date():
    return str(floor(time.time()*1000))

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
    URL = BASE_URL + args[0]
    proxies = {'https': 'http://137.123.%s.135:8134' % randint(2, 233)}
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
