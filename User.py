#!/usr/bin/env python
# encoding: utf-8

import getpass, re
from request import request
from captcha import request_captcha

class User():
    def __init__(self):
        print('@author: hxer')
        print('@contact: setup_@outlook.com')
        self.number = input('student number: ')
        self.collate('number')
        self.pwd = getpass.getpass('password: ')

    def collate(self, mode):
        if mode == 'number':
            if not self.number.isnumeric() or len(self.number) != 10 or not self.number.startswith('20'):
                self.number = input('  bad stutent number!!!\nretype your stduent number: ')
                self.collate('number')
        else:
            print("invaild password!, the wrong password is %s" % self.pwd)
            self.pwd = getpass.getpass('retype your password: ')

    def login(self):
        """fetch the main page(root directory) of tkkc website
        than set the cookie of JSESSIONID to login_header and captcha_header"""
        texts = request('').text
        login_cnt = 5
        while login_cnt > 0:
            annonuce = re.findall('<input type="hidden" name="(.*?)" value="announce"', texts, re.S)[0]
            login_url = re.findall('action="(.*?)"', texts, re.S)[0]

            captcha_code = request_captcha()
            data = {
                annonuce: 'announce',
                'loginMethod': annonuce + 'button',
                'logname': self.number,
                'password': self.pwd,
                'randomCode': captcha_code,
            }
            texts = request(login_url, data).text   # return loginMsg cookie
            login_cnt -= 1
            if texts.find('验证码错误') != -1:
                continue
            elif texts.find('密码不正确') != -1:
                self.collate('pwd')
            elif texts.find('服务器未建立连接') != -1:
                print('用户不存在或与身份验证服务器未建立连接！')
                exit()
            else:
                print("login success! Let's set sail!")
                break
