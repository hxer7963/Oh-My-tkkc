#!/usr/bin/env python
# encoding: utf-8

from request import request, session
import urllib

def request_captcha():
    # print(captcha_header['Cookie'])
    captcha_url = '/getRandomImage.do'
    im = request(captcha_url)
    image = urllib.parse.quote_from_bytes(im.content)
    captcha_code = session.post('http://api.hfutoyj.cn/codeapi', data={'image': image}).text
    print("captcha Code: ", captcha_code)
    return captcha_code

