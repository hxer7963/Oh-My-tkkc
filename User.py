#!/usr/bin/env python
# encoding: utf-8

import getpass, re, time
from collections import namedtuple

from tkkc_common import set_cookie, post, get
from tkkc_headers import *
from tkkc_captcha import request_capture

user = namedtuple('User', 'number pwd')
def user_info(student_num=None):
    type_num = 0
    while True:
        student_num = '2014211802'
        if student_num is None or type_num > 0:
            student_num = input('student_number: ').strip()
        if not student_num.isnumeric() or len(student_num) != 10 or not student_num.startswith('20'):
            type_num += 1
            print('学号输入错误, 请重新输入')
            continue
        # pwd = getpass.getpass('password: ').strip()
        pwd = 'hx123456'
        if not pwd:
            print('密码不能为空!')
            continue
        student = user(student_num, pwd)
        break
    return student


def user_login():
    print('@author: hxer')
    print('@contact: setup_@outlook.com')
    student = user_info()
    r = get('', tkkc_header)    # set-cookies: JSESSIONID
    annonuce = re.findall('<input type="hidden" name="(.*?)" value="announce"', r.text, re.S)[0]
    login_url = re.findall('action="(.*?)"', r.text, re.S)[0]
    set_cookie(login_header, 'JSESSIONID')
    set_cookie(capture_header, 'JSESSIONID')
    cnt = 0
    type_password_number = 0
    print('正在向服务器端提交用户数据...')
    while True:
        if cnt > 5:
            print('验证码错误次数过多，已退出程序')
            exit()
        capture_code = request_capture()
        data = {
            annonuce: 'announce',
            'loginMethod': annonuce + 'button',
            'logname': student.number,
            'password': student.pwd,
            'randomCode': capture_code,
        }
        texts = post(login_url, data, login_header).text   # return loginMsg cookie
        if texts.find('验证码错误') != -1:  # 学号、密码错误等等
            annonuce = re.findall('<input type="hidden" name="(.*?)" value="announce"', texts, re.S)[0]     # 每次验证码错误都会换announce
            cnt += 1
            time.sleep(0.05)
        elif texts.find('密码不正确') != -1:
            print('密码不正确,当前输入的密码为: {}'.format(student.pwd))
            type_password_number += 1
            if type_password_number > 2:
                print('密码错误三次，程序自动退出，请核对后重新输入！')
                exit()
            student = user_info(student.number)
        elif texts.find('服务器未建立连接') != -1:
            print('用户不存在或与身份验证服务器未建立连接！')
            exit()
        else:
            break
