#!/usr/bin/env python
# encoding: utf-8

from tkkc_common import get, post, session
from tkkc_headers import capture_header


def request_capture():
    # print(capture_header['Cookie'])
    capture_url = '/getRandomImage.do'
    im = get(capture_url, capture_header)
    import urllib
    image = urllib.parse.quote_from_bytes(im.content)
    capture_code = session.post('http://api.hfutoyj.cn/codeapi', data={'image': image}).text
    print("capture Code: ", capture_code)
    return capture_code

