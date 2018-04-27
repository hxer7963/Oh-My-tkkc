#!/usr/bin/env python
# encoding: utf-8

from tkkc_common import get, post, session
from tkkc_headers import captcha_header


def request_captcha():
    # print(captcha_header['Cookie'])
    captcha_url = '/getRandomImage.do'
    im = get(captcha_url, captcha_header)
    import urllib
    image = urllib.parse.quote_from_bytes(im.content)
    captcha_code = session.post('http://api.hfutoyj.cn/codeapi', data={'image': image}).text
    print("captcha Code: ", captcha_code)
    return captcha_code

