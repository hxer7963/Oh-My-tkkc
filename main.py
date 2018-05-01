# encoding=utf-8
"""
@author: hxer
@contact: hxer7963@gmail.com
@time: 2017/4/21 23:08
"""
from course import course, main_page
from User import User


def main():
    user = User()
    user.login()
    courses_list = main_page()
    abstracts = []
    for name, href in courses_list:
        abstracts.append(course(name, href))
    abstracts = [_ for _ in abstracts if _.strip()]
    if abstracts:
        print('-'*40, '\n'.join([_ for _ in abstracts]), sep='\n')
        print('-'*40)
        print('请登录http://tkkc.hfut.edu.cn **提交作业**, 未完成的题目还需自行补题')

if __name__ == '__main__':
    main()
