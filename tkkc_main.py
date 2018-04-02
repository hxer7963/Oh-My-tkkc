# encoding=utf-8
"""
@author: hxer
@contact: hxer7963@gmail.com
@time: 2017/4/21 23:08
"""
import os
import time
from tkkc_implement import index_page, courses_homepage, bbs_page, bbs_task, task_assignment, assignment_document, manage_exam
from xls_data_process import download_xls, xlsx_directory, delete_xlsx
from User import user_login


def main():
    user_login()
    start_time = time.time()
    try:
        courses = index_page()
    except IndexError:
        print('当前用户尚未加入到系统中，请确认账号是否正确，以及本期是否有选课！')
        exit()
    abstract = []
    for course_name in courses.keys():
        course_url = courses[course_name]
        try:
            learning_url, bbs_url = courses_homepage(course_name, course_url)
        except TimeoutError as exc:
            print(exc)
            continue
        course_id = course_url.split('&')[-1].split('=')[-1]
        teaching_task_id = learning_url.split('&')[-1].split('=')[-1]
        # 获取交流界面，查看是否需要评论
        forum_id, discuss_cnt, entities = bbs_page(bbs_url, course_name)
        # 进入学习 获取课程任务页面：题库下载、自测、考试
        resource_url, exam_time, task_queue = task_assignment(learning_url, teaching_task_id, forum_id)  # 返回set，存储各测试的url
        # 进行评论
        if discuss_cnt > 0 and entities:
            bbs_task(course_name, teaching_task_id, course_id, forum_id, resource_url, discuss_cnt, entities)
        exam = True
        xls_download = False
        unfinished_num = 0

        for category in task_queue.keys():  # 使用多线程，assignment_document请求document，manage_exam中请求xhr
            try:
                task_url = task_queue[category]
                questions_set = assignment_document(task_url)  # 请求任务document
            except TimeoutError as timeout:
                exam = False
                print('{}'.format(course_name), timeout)
            else:
                unfinished_num = len(questions_set.exercise_set)
                if unfinished_num == 0:
                    abstract.append('好气啊!{} {}保存好了竟然忘了提交作业******请尽快提交该题作业!'.
                                    format(course_name, category))
                    time.sleep(1)
                else:
                    print('好气啊!{} {}还有{}道题目未做....'.format(course_name, category, unfinished_num))
                    if not xls_download:
                        download_xls(course_name, resource_url)
                    xls_download = True
                    time_stamp = time.time()
                    manage_exam(course_name, questions_set)
                    if unfinished_num != 0:
                        finished_info = '{}{}已完成,共保存{}题,用时{}s，请手动提交作业........'.\
                            format(course_name, category,  unfinished_num, int(time.time()-time_stamp))
                        print(finished_info)
                        abstract.append(finished_info)

        if xls_download:
            print('')
            delete_xlsx(course_name)
        if not exam:
            if unfinished_num != 0:
                print('{}课程自测任务已经完成,用时{}s，请手动提交作业。'.format(course_name, int(time.time() - time_stamp)))
            print('提示：考试“截止”时间为：{}。'.format(exam_time))
        elif task_queue:
            exam_finished_info = '{}课程考试题目已保存，请手动提交考试作业 >>希望没挂...<<'.format(course_name)
            print(exam_finished_info)
            abstract.append(exam_finished_info)
    if abstract:
        print('当前任务全都保存成功~~ 总耗时用时{}s，以下是需要提交的作业摘要'.format(int(time.time() - start_time)))
        print('-'*40)
        for info in abstract:
            print(info)
        print('-'*40)
        print('请登录http://tkkc.hfut.edu.cn 提交作业<注意确认 "多选题" 是否成功提交，出现异常请联系 setup_@outlook.com')
    delete_xlsx()

if __name__ == '__main__':
    main()
