# Oh-My-tkkc

oh-my-tkkc is a complete automatic crawler pragram which only need to type your student num and password in [tkkc](tkkc.hfut.edu.cn), then it will identification verfication code by send the bytes of captcha to [API](http://api.hfutoyi/codeapi), What you need to do is **just** to check the result and file *your* exercise or exam to server.

To learn more, visit [ohmytkkc](http:hxer.me/).

## Getting Started

#### Prerequisits

* python3 should be installed on your platform.
* git should be installed.2

#### Installion

Oh-My-tkkc is installed by running one of the following commands in your terminal.

```Shell
$ git clone https://github.com/hxer7963/Oh-My-tkkc.git
```

##### install dependencies with pip

```shell
$ pip install --upgrade pip
$ sudo pip install virtualenv
$ virtualenv --version
$ virtualenv tkkc -p /usr/bin/python3.5
$ source tkkc/bin/activate
(tkkc) $ pip --version
pip 9.0.3 from /home/hxer/Oh-My-tkkc/tkkc/lib/python3.5/site-packages (python 3.5)
(tkkc) $ pip install requests lxml Pillow xlrd rarfile
```

##### Launch it

```shell
(tkkc) $ python tkkc_main.py
```

Type your personal details included student num and password, if password invalid, Oh-My-tkkc will explicit in plain-text in terminal ! When it finished, Don't forget to open the [URL](http://tkkc.hfut.edu.cn) to file your exercise/exam. enjoying it !
