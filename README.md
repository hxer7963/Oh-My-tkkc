#Oh-My-tkkc

oh-my-tkkc is a complete automatic crawler pragram which only need to type your student num and password in [tkkc](http://tkkc.hfut.edu.cn), then it will identification verfication code by send the bytes of captcha to `api.hfutoyi`, What you need to do is **just** to check the result and file *your* exercise or exam to server.

To learn more, visit [oh-my-tkkc](https://hxer.me/post/cb3e52e1.html).

## Getting Started

#### Prerequisits

* python3 should be installed on your platform. [Using Python on Windows](https://docs.python.org/3/using/windows.html) 
* UnRaR.exe should be installed on your **platform**。

#### Installion

Oh-My-tkkc is installed by running one of the following commands in your terminal.

```Shell
$ git clone https://github.com/hxer7963/Oh-My-tkkc.git
```

You can also be free to download it by manual.

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

##### install UnRAR on your Platform

Because the type of compressed file is rar, And rarfile third-party library is used in the code just as you can see the dependences above.

* Windows Platform

  * Download [UnRAR](https://www.rarlab.com/rar_add.htm), two-click to install, then you'll get `UnRAR.exe`file.
  * Locate the rarfile.py file just type the follow command.

  ```shell
  (tkkc) $ python -c "import rarfile; print(rarfile.__file__)"
  ```

  * Modify the `UNRAR_TOOL=r"the path of UnRAR.exe"`;

  see [details](https://stackoverflow.com/questions/17614467/how-can-unrar-a-file-with-python) 

* Linux

  `sudo apt-get install unrar-free`

* MAC OS X

  `brew install unrar`

##### Launch it

```shell
(tkkc) $ python tkkc_main.py
```

Type your personal details included student num and password, if password invalid, Oh-My-tkkc will explicit in plain-text in terminal ! When it finished, Don't forget to open the [tkkc](http://tkkc.hfut.edu.cn) to file your exercise/exam. enjoying it !