# encoding=utf-8
"""
@author: hxer
@contact: hxer7963@gmail.com
@time: 2017/4/21 23:08
"""
import sys, re, time
from collections import namedtuple
from lxml import html
from PIL import Image

from tkkc_common import date, post, get, session, set_cookie
from xls_data_process import xls_search_answer, json_extract, question_extract
from tkkc_headers import tkkc_header, login_header, xhr_header, document_header, \
    save_answer_headers, index_header, capture_header
from User import user


def index_page():
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
    print(' '.join(info))      # 输出用户信息
    course = {}
    list_course = tree.xpath('//ul[@class="subNav"]')[0]
    for node in list_course.xpath('./li'):
        href = node.get('onclick').split("'")[1]
        name = node.xpath('./span/@title')[0]
        course[name] = href  # 课程及href
    print('您有{}门试题库，分别为: {}'.format(len(course), ' '.join(course.keys())))
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

# 请求“交流”页面，同时获取高跟帖问题
def bbs_page(bbs_url, name):
    status = get(bbs_url, index_header)
    index_header['Referer'] = bbs_url
    tree = html.fromstring(status.text)
    user_info = tree.xpath('//div[@class="bottom"]')[0].text.split()[:-1][-1]
    questions = tree.xpath('//tr[@class="a"]')
    entities = []
    for question in questions:
        qst = question.xpath('td/a/text()')[0].strip()
        comments = int([item.strip() for item in question.xpath('td/text()') if item.strip()][1])
        entities.append([comments, qst])
    entities.sort(reverse=True)
    user_name_num = len(re.findall(user_info, status.text))
    discuss_cnt = 3 - user_name_num  # 还需评论数
    forum_id = '&forumId=(.*?)&'  # forumId=
    forum_id = re.search(forum_id, status.text).group(1)
    if len(entities) > 10:
        entities = entities[:10]
    return forum_id, discuss_cnt, entities


def bbs_task(name, teaching_task_id, course_id, forum_id, resource_url, discuss_cnt, questions):     # 提问题
    # 不再从xlsx中获取题目，而是从已经发布的页面获取跟帖较高的题目
    # questions = question_extract(name, resource_url, discuss_cnt)
    print('{}课程还需评论{}次'.format(name, discuss_cnt))
    # print('bbs_task len(questions) =', len(questions))
    idx = -1
    for i in range(discuss_cnt):
        from random import randint
        aux = randint(0, len(questions))
        while idx == aux and len(questions) > 1:
            aux = randint(0, len(questions))
        idx = aux
        post_url = '/student/bbs/manageDiscuss.do?{}&method=toAdd&teachingTaskId={}&forumId={}&' \
                                 'isModerator=false'.format(date(), teaching_task_id, forum_id)
        status = get(post_url, index_header)    # 获取发布讨论的网页

        data = {
            'forumId': forum_id,
            'teachingTaskId': teaching_task_id,
            'isModerator': 'false',
            'topic': questions[idx][1],
            'content': questions[idx][1],
        }
        dispatch = '/student/bbs/manageDiscuss.do?{}&method=add'.format(date())
        post(dispatch, data, index_header)  # 这是一个302转发
        bbs_index = '/student/bbs/index.do?teachingTaskId={}&forumId={}&{}&'\
            .format(teaching_task_id, course_id, date())  # 直接添加就行
        get(bbs_index, index_header)
        print('讨论问题：{}'.format(questions[idx][1]))
    return forum_id


def task_assignment(task_homepage, teaching_task_id, forum_id):     # 获取自测url
    refer = 'http://tkkc.hfut.edu.cn/student/bbs/index.do?teachingTaskId={}&forumId={}&{}&'
    index_header['Referer'] = refer.format(teaching_task_id, forum_id, date())
    status = get(task_homepage, index_header)  # 进入主页面
    index_header['Referer'] = task_homepage
    texts = status.text
    tree = html.fromstring(texts)
    tr = tree.xpath('//tr[@class="a"]')
    questions_set = {}
    for task in tr:
        category = task.xpath('.//td[@title]')[0].text.strip()
        if category == '题库下载':
            resource_url = task.xpath('.//a/@href')[0]
        else:
            try:
                completed = task.xpath('.//a[@href]')[0]    # 是否已完成任务
            except IndexError as index_error:
                completed.text = '查看任务'     # 考完试后，不能查看，即没有<a href>的标签
            if completed.text == '进入任务':
                task_url = completed.get('href')
                questions_set[category] = task_url
            else:
                score = task.xpath('./td[5]')[0].text.strip()  # 完成的输出以提示
                print(category, score, '..................')
            if category == '考试':
                exam_time = task.xpath('./td[4]')[0].text.strip()
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
        raise TimeoutError('目前考试未开始')
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
    exercise_set = re.findall(exercise_id, text)
    date_time = '/student/exam/manageExam.do?(.*?)&method=getExerciseInfo'
    date_time = re.search(date_time, text).group(1)[1:]
    const = constant(date_time=date_time, examReplyId=exam_reply_id, examId=exam_id,
                     teachingTaskId=teaching_task_id, exercise_set=exercise_set)
    return const


def xhr_question(date_time, reply_id, student_exercise_id, exercise_id):
    url = '/student/exam/manageExam.do'
    data = {
        '{}'.format(date_time): '',
        'method': 'getExerciseInfo',
        'examReplyId': reply_id,
        'exerciseId': exercise_id,
        'examStudentExerciseId': student_exercise_id,
    }
    r = post(url, data, xhr_header)  # json
    assert 'optionsC' in r.json()
    return r.json()


def manage_exam(course_name, assignment):
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
    for examStudentExerciseId, exerciseId, count in assignment.exercise_set:
        json = xhr_question(date_time, exam_reply_id,  examStudentExerciseId, exerciseId)
        types = json['type']
        try:
            title, options_answers, category = json_extract(count, json)
            answer = xls_search_answer(title, options_answers, category, course_name)
        except ValueError as exc:   # 没有找打就不保存题目，直接下一题
            print(exc, '没有保存该题，请手动提交时补写')
        else:
            data['examStudentExerciseId'] = examStudentExerciseId
            data['exerciseId'] = exerciseId
            print('正在保存...', end=' ')
            sys.stdout.flush()
            for i in range(3):
                status = save_answer(types, answer, data)
                if status["status"] == 'fail':    # 失败了继续提交到队列中
                    time.sleep(0.3)
                    save_answer(types, answer, data)
                    print('保存失败...正在尝试再次保存此题')
                    if i == 2:
                        assignment.exercise_set.append((examStudentExerciseId, exerciseId, count))
                        print('网络太拥塞了，题目保存三次都失败了..，稍后再尝试提交这道题...')
                else:
                    print('保存成功')
                    break

"""
duoxAnswer:A,B,C
DXanswer:B
DuoXanswerA:A
DuoXanswerB:B
DuoXanswerC:C
"""
def save_answer(types, answers_list, data):
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
    # if types != 4:
    #     print('非多选题，不必重做', end=' ')
    #     sys.stdout.flush()
    #     return {"status": "ok"}
    hand_url = '/student/exam/manageExam.do?{}&method=saveAnswer'.format(date())
    response = post(hand_url, data_copy, save_answer_headers)   # response "status": "ok"
    return response.json()    # AssertionError
