# encoding=utf-8
"""
@author: hxer
@contact: hxer7963@gmail.com
@time: 2017/4/21 23:38
"""
import time
from math import floor
import functools
from requests import Session, exceptions
from random import randint
from collections import namedtuple


def set_cookie(header, key):
    if key in session.cookies:
        cookie = session.cookies[key]
        header['Cookie'] += key + '=' + cookie + '; '


def get_proxies():
    return 'http://137.123.' + str(randint(2, 200)) + '.135:8084'


proxies = {'https': ''}
BASE_URL = 'http://tkkc.hfut.edu.cn'
session = Session()


def write2file(filename, texts):
    with open(filename, 'w') as wt:
        wt.write(texts)


def date():
    return str(floor(time.time()*1000))


def decorate(func):
    @functools.wraps(func)
    def wrapper(*args):    # url, data return content
        try:
            response = func(*args)
        except exceptions.ReadTimeout as exc:
            print(exc)
            exit()
        except exceptions.HTTPError as exc:
            print(*args[0], 'status_code:', exc.response)
            exit()
        except exceptions.ConnectionError as exc:
            print(exc)
            exit()
        else:
            try:
                response.raise_for_status()
            except UnboundLocalError as exc:    # 请求失败
                print(exc)
                exit()
            except exceptions.HTTPError as exc:     # 状态码错误
                print(exc)
                exit()
            else:
                return response
    return wrapper


@decorate
def get(url, header):
    url = BASE_URL + url
    print(url)
    proxies['https'] = get_proxies()
    return session.get(url, headers=header, proxies=proxies, timeout=1000)


@decorate
def post(url, data, header):
    url = BASE_URL + url
    proxies['https'] = get_proxies()
    return session.post(url, data=data, headers=header, proxies=proxies, timeout=1000)
