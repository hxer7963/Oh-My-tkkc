# encoding=utf-8
"""
@author: hxer
@contact: hxer7963@gmail.com
@time: 2017/4/21 23:08
"""
import sys, re
from collections import namedtuple
from lxml import html
from PIL import Image
import requests

from tkkc_common import date, post, get, session, set_cookie
from xls_data_process import xls_search_answer, json_extract
from tkkc_headers import tkkc_header, login_header, xhr_header, document_header, \
    save_answer_headers, index_header, capture_header


def main_page():
    index_url = '/student/index.do?{}&'.format(date())   # 作为之后登陆的Referer
    set_cookie(index_header, 'JSESSIONID')
    index_header['Cookie'] += '; '
    set_cookie(index_header, 'loginedMsg')
    response = get(index_url, index_header)
    index_header['Referer'] = index_url

    document_header['Cookie'] = index_header['Cookie']
    document_header['Referer'] = index_header['Referer']

    text = response.text
    tree = html.fromstring(text)
    info = tree.xpath('//div[@class="bottom"]')[0].text.split()[:-1]
    print(' '.join(info))
    course = {}
    list_course = tree.xpath('//ul[@class="subNav"]')[0]
    for node in list_course.xpath('./li'):
        href = node.get('onclick').split("'")[1]
        name = node.xpath('./span/@title')[0]
        course[name] = href  # 课程及href
    print('您有{}门试题库: {}'.format(len(course), ', '.join(course.keys())))
    if len(course) == 0:   # 没有选修课程肯定是进不去的，所以应该在登录界面进行re匹配特定的alert
        print('没选试题库？')
        exit()
    return course


def courses_homepage(name, course_url):
    response = get(course_url, index_header)   # 可能是还未开课
    index_header['Referer'] = course_url
    texts = response.text
    homepage_closed = '课程开始时间：(.*?)，暂时不能进入学习！'
    begin_time = re.search(homepage_closed, texts)
    if begin_time:  # setup() 定时刷课程序
        raise TimeoutError(name + '课程开始时间:', begin_time.group(1), '暂时不能进入学习')
    if texts.find('课程已结束') != -1:
        raise TimeoutError('{} 课程已结束，不能进入学习了！'.format(name))
    homepage = html.fromstring(texts)
    tasks = homepage.xpath('//li[@class="item "]')  # //table[@id="insideNav"]
    task_homepage = tasks[0].get('onclick').split("'")[1]
    bbs = tasks[-1].get('onclick').split("'")[1]
    return task_homepage, bbs   # 当前任务、交流 url


def extract_qst(href):
    tree = html.fromstring(get(href, index_header).text)
    title = tree.xpath('//div[@class="assignment-head"]/text()')
    content = tree.xpath('//div[@class="BbsContent"]/span//text()')
    if not content:
        content = title[0].strip()
    else:
        content = '\n'.join([stm.strip() for stm in content])
    return (title[0].strip(), content)


# 请求“交流”页面，同时获取高跟帖问题
def bbs_page(bbs_url, name):
    status = get(bbs_url, index_header)
    index_header['Referer'] = bbs_url
    tree = html.fromstring(status.text)
    user_info = tree.xpath('//div[@class="bottom"]')[0].text.split()[:-1][-1]
    questions = tree.xpath('//tr[@class="a"]')
    entities = []
    for question in questions:
        qst_href = question.xpath('td/a/@href')[0].strip()
        comments = int([item.strip() for item in question.xpath('td/text()') if item.strip()][1])
        entities.append((comments, qst_href))
    entities.sort()
    user_name_num = len(re.findall(user_info, status.text))
    discuss_cnt = 3 - user_name_num  # 还需评论数
    forum_id = '&forumId=(.*?)&'  # forumId=
    forum_id = re.search(forum_id, status.text).group(1)
    if len(entities) > 13:
        entities = entities[-13:]
    return forum_id, discuss_cnt, entities


def bbs_task(name, teaching_task_id, course_id, forum_id, dis_cnt, questions):     # 提问题
    from random import choice
    hrefs = [choice(questions)[1] for _ in range(dis_cnt)]
    qst = [extract_qst(href) for href in hrefs]
    for i in range(dis_cnt):
        post_url = '/student/bbs/manageDiscuss.do?{}&method=toAdd&teachingTaskId={}&forumId={}&' \
                                 'isModerator=false'.format(date(), teaching_task_id, forum_id)
        get(post_url, index_header)    # 获取发布讨论的网页
        data = {
            'forumId': forum_id,
            'teachingTaskId': teaching_task_id,
            'isModerator': 'false',
            'topic': qst[i][0],
            'content': qst[i][1],
        }
        dispatch = '/student/bbs/manageDiscuss.do?{}&method=add'.format(date())
        post(dispatch, data, index_header)  # 这是一个302转发
        bbs_index = '/student/bbs/index.do?teachingTaskId={}&forumId={}&{}&'\
            .format(teaching_task_id, course_id, date())  # 直接添加就行
        get(bbs_index, index_header)
        print('讨论问题->标题:{}, 内容:{}'.format(*qst[i]))
    return forum_id


def task_assignment(task_homepage, teaching_task_id, forum_id):     # 获取自测url
    refer = 'http://tkkc.hfut.edu.cn/student/bbs/index.do?teachingTaskId={}&forumId={}&{}&'
    index_header['Referer'] = refer.format(teaching_task_id, forum_id, date())
    status = get(task_homepage, index_header)  # 进入主页面
    index_header['Referer'] = task_homepage
    texts = status.text
    tree = html.fromstring(texts)
    cur_state_idx = [_.strip() for _ in tree.xpath('//tr[@class="bg_tr"]/th/text()') if _.strip()].index('当前状态')
    tr = tree.xpath('//tr[@class="a"]')
    questions_set = {}
    for task in tr:
        category = task.xpath('.//td[@title]')[0].text.strip()
        if category == '题库下载':
            resource_url = task.xpath('.//a/@href')[0]
        else:
            if category == '考试':
                exam_time = task.xpath('./td[4]')[0].text.strip()
            cur_state = [_.strip() for _ in task.xpath('./td//text()') if _.strip()]
            if '已完成' in cur_state[cur_state_idx]:
                print('%s %s ^_^' % (cur_state[1], cur_state[cur_state_idx]))
                continue
            completed = task.xpath('.//a[@href]')[0]  # 没有完成任务则给出链接
            task_url = completed.get('href')
            questions_set[category] = task_url
    return resource_url, exam_time, questions_set     # 答题的链接
# examReplyId examId teachingTaskId在不同的自测任务中不同。exercise_set为list, 每道题不同.
constant = namedtuple('Constant', 'date_time examReplyId examId teachingTaskId exercise_set')


def assignment_document(task_url):  # 获取没有加载xhr题目的页面，得到xhr的参数
    status = get(task_url, document_header)
    save_answer_headers['Referer'] = xhr_header['Referer'] = task_url
    save_answer_headers['Cookie'] = xhr_header['Cookie'] = index_header['Cookie']
    text = status.text
    alert = '任务未开始'
    if re.search(alert, text):
        raise ValueError('目前考试未开始')
    xhr_header['Referer'] = task_url
    save_answer_headers['Referer'] = task_url
    # xpath to get examReplyId examId teachingTaskId in Form
    tree = html.fromstring(text)
    form_input = tree.xpath('//*[@id="saveAnswerForm"]')[0]
    exam_reply_id = form_input.xpath('//*[@id="examReplyId"]/@value')[0]
    exam_id = form_input.xpath('//*[@id="examId"]/@value')[0]
    teaching_task_id = form_input.xpath('//*[@id="teachingTaskId"]/@value')[0]
    # print(exam_reply_id, exam_id, teaching_task_id)

    exercise_id = '"complete":false,"examStudentExerciseId":(.*?),"exerciseId":(.*?),"index":(.*?)}'  #
    exercise_set = [(exam, Id, int(idx)) for exam, Id, idx in re.findall(exercise_id, text)]
    if 1 < len(exercise_set) < 20:
        from operator import itemgetter
        exercise_set.sort(key=itemgetter(2))
        if exercise_set[0][2] != exercise_set[1][2]-1 and exercise_set[-2][2] != exercise_set[-1][2]-1:
            raise ValueError('当前还有{}道题没找到答案,题号为: {}'.format(len(exercise_set), ','.join([str(item[2]) for item in exercise_set])))
    date_time = '/student/exam/manageExam.do?(.*?)&method=getExerciseInfo'
    date_time = re.search(date_time, text).group(1)[1:]
    const = constant(date_time=date_time, examReplyId=exam_reply_id, examId=exam_id,
                     teachingTaskId=teaching_task_id, exercise_set=exercise_set)
    return const


def xhr_question(date_time, reply_id, student_exercise_id, exercise_id):
    url = '/student/exam/manageExam.do'
    data = {
        str(date_time): '',
        'method': 'getExerciseInfo',
        'examReplyId': reply_id,
        'exerciseId': exercise_id,
        'examStudentExerciseId': student_exercise_id,
    }
    r = post(url, data, xhr_header)  # json
    assert 'optionsC' in r.json()
    return r.json()


def manage_exam(xls_dict, course_name, assignment):
    date_time = assignment.date_time
    exam_reply_id = assignment.examReplyId
    data = {
        'examReplyId': exam_reply_id,
        'examStudentExerciseId': '',
        'exerciseId': '',
        'examId': assignment.examId,
        'teachingTaskId': assignment.teachingTaskId,
        'content': '',
    }
    idx = 1
    for examStudentExerciseId, exerciseId, count in assignment.exercise_set:
        json = xhr_question(date_time, exam_reply_id,  examStudentExerciseId, exerciseId)
        try:
            title, options_answers, category = json_extract(json)
            print(str(idx) + '.', title); idx += 1
            answer = xls_search_answer(xls_dict, title, options_answers, category)
        except ValueError as exc:   # 没有找打就不保存题目，直接下一题
            print('没有找到答案, 请自行补题:-)')
        else:
            data['examStudentExerciseId'] = examStudentExerciseId
            data['exerciseId'] = exerciseId
            print('答案为:', ' '.join(answer))
            print('正在保存...', end=' ')
            sys.stdout.flush()
            types = json['type']
            for i in range(3):
                try:
                    save_answer(types, answer, data)
                except requests.exceptions.ConnectionError as ce:
                    print(ce)
                    if i == 2:
                        assignment.exercise_set.append((examStudentExerciseId, exerciseId, count))
                else:
                    print('保存成功')
                    break

def save_answer(types, answers_list, data):
    """
    duoxAnswer:A,B,C DXanswer:B DuoXanswerA:A
    DuoXanswerB:B DuoXanswerC:C
    """
    data_copy = data.copy()
    if types == 1:
        prefix = 'DXanswer'
    elif types == 4:
        prefix = 'DuoXanswer{}'
        data_copy['duoxAnswer'] = ','.join(answers_list)    # 考试时，多选题多了一个Json数据
    else:   # 好像多了一个单选A DXanswer: A
        prefix = 'PDanswer'
    if types != 4:
        data_copy[prefix] = answers_list[0]  # answers_list[0]
    else:
        data_copy['duoxAnswer'] = ','.join(answers_list)
        for answer in answers_list:
            key = prefix.format(answer)
            data_copy[key] = 'true'     # 切莫用data，因为传过来的data是按址传参的...
    hand_url = '/student/exam/manageExam.do?{}&method=saveAnswer'.format(date())
    try:
        response = post(hand_url, data_copy, save_answer_headers)   # response "status": "ok"
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Connection aborted.', RemoteDisconnected('Remote end closed connection without response',)")
    return response.json()    # AssertionError
