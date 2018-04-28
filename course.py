# encoding=utf-8
"""
@author: hxer
@contact: hxer7963@gmail.com
@time: 2017/4/21 23:08
"""
import sys, re
from collections import namedtuple
from lxml import html
from time import perf_counter as pc
from request import date, request
from xls_data_process import xls_search_answer, json_extract


def main_page():
    index_url = '/student/index.do?{}&'.format(date())   # 作为之后登陆的Referer
    text = request(index_url).text
    tree = html.fromstring(text)
    user_info = tree.xpath('//div[@class="bottom"]')[0].text.split()[:-1]
    print(' '.join(user_info))
    course_list = []
    list_course = tree.xpath('//ul[@class="subNav"]')[0]
    for node in list_course.xpath('./li'):
        course_homepage_href = node.get('onclick').split("'")[1]
        course_name = node.xpath('./span/@title')[0]
        course_list.append((course_name, course_homepage_href))
    print('您有{}门试题库: {}'.format(len(course_list), ', '.join([course_name for course_name, _ in course_list])))
    return course_list

def course(name, course_homepage_href):
    try:
        learning_url, bbs_url = courses_homepage(name, course_homepage_href)
    except TimeoutError as te:
        print(te)
        return
    course_id = course_homepage_href.split('&')[-1].split('=')[-1]
    teaching_task_id = learning_url.split('&')[-1].split('=')[-1]
    # 获取交流界面，查看是否需要评论
    forum_id, discuss_cnt, bbs_hrefs = bbs_page(bbs_url, name)
    if discuss_cnt > 0 and bbs_hrefs: # disuss
        bbs_task(name, teaching_task_id, course_id, forum_id, discuss_cnt, bbs_hrefs)
    # 进入学习 获取课程任务页面：题库下载、自测、考试
    resource_url, exam_time, tasks = task_assignment(learning_url, teaching_task_id, forum_id)  # 返回set，存储各测试的url
    course_abstract = []
    for category, task_url in tasks:  # 使用多线程，assignment_document请求document，manage_exam中请求xhr
        try:
            questions_set = assignment_document(name, task_url)  # 请求任务document
            unfinished_num = len(questions_set.exercises_id)
        except ValueError as ve:
            print(ve)
            course_abstract.append('{}课程*考试*截止时间为:{}'.format(name, exam_time))
        else:
            print('好气啊!{}{}还有{}道题目未做....'.format(name, category, unfinished_num))
            from xls_data_process import excel_dict
            xls_dict = excel_dict(resource_url)     # 获取excel文件hash title存储到dict中
            time_stamp = pc()
            manage_exam(xls_dict, name, questions_set)
            FMT = '{}{}已完成,共保存{}题,用时{:.2f}s;'
            printInfo = FMT.format(name, category,  unfinished_num, pc()-time_stamp)
            print(printInfo)
            course_abstract.append(printInfo)
    return '\n'.join([_ for _ in course_abstract])



def courses_homepage(name, course_url):
    """ check the time and return the task_homepage with the bbs discuss href"""
    texts = request(course_url).text
    homepage_closed = '课程开始时间：(.*?)，暂时不能进入学习！'
    t0 = re.search(homepage_closed, texts)
    if t0:
        raise TimeoutError('{}课程开始时间:{}, 暂时不能进入学习'.format(name, t0.group(1)))
        # raise TimeoutError('%s课程开始时间:%r,暂时不能进入学习', % (name, begin_time.group(1)))
    if texts.find('课程已结束') != -1:
        raise TimeoutError('{}课程已结束，不能进入学习'.format(name))
    homepage = html.fromstring(texts)
    tasks = homepage.xpath('//li[@class="item "]')  # //table[@id="insideNav"]
    task_homepage = tasks[0].get('onclick').split("'")[1]
    bbs = tasks[-1].get('onclick').split("'")[1]
    return task_homepage, bbs   # 进入学习 and 交流 页面


def extract_qst(href):
    text = request(href).text
    tree = html.fromstring(text)
    title = tree.xpath('//div[@class="assignment-head"]/text()')
    content = tree.xpath('//div[@class="BbsContent"]/span//text()')
    if not content:
        content = title[0].strip()
    else:
        content = '\n'.join([stm.strip() for stm in content])
    return (title[0].strip(), content)


# 请求“交流”页面，同时获取高跟帖问题
def bbs_page(bbs_url, name):
    text = request(bbs_url).text
    tree = html.fromstring(text)
    user_info = tree.xpath('//div[@class="bottom"]')[0].text.split()[:-1][-1]
    questions = tree.xpath('//tr[@class="a"]')
    entities = []
    for question in questions:
        qst_href = question.xpath('td/a/@href')[0].strip()
        comments = int([item.strip() for item in question.xpath('td/text()') if item.strip()][1])
        entities.append((comments, qst_href))
    entities.sort()
    user_name_num = len(re.findall(user_info, text))
    discuss_cnt = 3 - user_name_num  # 还需评论数
    forum_id = '&forumId=(.*?)&'  # forumId=
    forum_id = re.search(forum_id, text).group(1)
    if len(entities) > 13:
        entities = entities[-13:]
    hrefs = [href for _, href in entities]
    return forum_id, discuss_cnt, hrefs


def bbs_task(name, teaching_task_id, course_id, forum_id, dis_cnt, qst_href):     # 提问题
    from random import choice
    hrefs = [choice(qst_href) for _ in range(dis_cnt)]
    qst = [extract_qst(href) for href in hrefs]
    for i in range(dis_cnt):
        post_url = '/student/bbs/manageDiscuss.do?{}&method=toAdd&teachingTaskId={}&forumId={}&' \
                                 'isModerator=false'.format(date(), teaching_task_id, forum_id)
        request(post_url)    # 获取发布讨论的网页
        data = {
            'forumId': forum_id,
            'teachingTaskId': teaching_task_id,
            'isModerator': 'false',
            'topic': qst[i][0],
            'content': qst[i][1],
        }
        dispatch = '/student/bbs/manageDiscuss.do?{}&method=add'.format(date())
        request(dispatch, data)  # 这是一个302转发
        # bbs_index = '/student/bbs/index.do?teachingTaskId={}&forumId={}&{}&'\
            # .format(teaching_task_id, course_id, date())  # 直接添加就行
        # request(bbs_index)
        print('讨论问题->标题:{}\n内容:{}'.format(*qst[i]))
    return forum_id


def task_assignment(task_homepage, teaching_task_id, forum_id):     # 获取自测url
    texts = request(task_homepage).text  # 进入主页面
    tree = html.fromstring(texts)
    cur_state_idx = [_.strip() for _ in tree.xpath('//tr[@class="bg_tr"]/th/text()') if _.strip()].index('当前状态')
    tr = tree.xpath('//tr[@class="a"]')
    tasks = []
    for task in tr:
        category = task.xpath('.//td[@title]')[0].text.strip()
        if category == '题库下载':
            resource_url = task.xpath('.//a/@href')[0]
        else:
            if category == '考试':
                exam_time = task.xpath('./td[4]')[0].text.strip()
            cur_state = [_.strip() for _ in task.xpath('./td//text()') if _.strip()]
            if '分' in cur_state[cur_state_idx]:
                print('%s %s ^_^' % (cur_state[1], cur_state[cur_state_idx]))
                continue
            task_url = task.xpath('.//a/@href')[0]  # 没有完成任务则给出链接
            tasks.append((category, task_url))
    return resource_url, exam_time, tasks     # 答题的链接
# examReplyId examId teachingTaskId在不同的自测任务中不同。exercises_id为list, 每道题不同.
constant = namedtuple('Constant', 'date_time examReplyId examId teachingTaskId exercises_id')


def assignment_document(name, task_url):  # 获取没有加载xhr题目的页面，得到xhr的参数
    text = request(task_url).text
    alert = '任务未开始'
    if re.search(alert, text):
        raise ValueError('目前{}课程*考试*未开始'.format(name))
    # xpath to get examReplyId examId teachingTaskId in Form
    tree = html.fromstring(text)
    form_input = tree.xpath('//*[@id="saveAnswerForm"]')[0]
    exam_reply_id = form_input.xpath('//*[@id="examReplyId"]/@value')[0]
    exam_id = form_input.xpath('//*[@id="examId"]/@value')[0]
    teaching_task_id = form_input.xpath('//*[@id="teachingTaskId"]/@value')[0]
    # print(exam_reply_id, exam_id, teaching_task_id)

    exercise_id = '"complete":false,"examStudentExerciseId":(.*?),"exerciseId":(.*?),"index":(.*?)}'  #
    exercises_id = [(exam, Id, int(idx)) for exam, Id, idx in re.findall(exercise_id, text)]
    if 1 < len(exercises_id) < 15:
        from operator import itemgetter
        exercises_id.sort(key=itemgetter(2))
        if exercises_id[0][2] != exercises_id[1][2]-1 and exercises_id[-2][2] != exercises_id[-1][2]-1:
            raise ValueError('当前还有{}道题没找到答案,题号为: {}'.format(len(exercises_id), ', '.join([str(item[2]) for item in exercises_id])))
    date_time = '/student/exam/manageExam.do?(.*?)&method=getExerciseInfo'
    date_time = re.search(date_time, text).group(1)[1:]
    const = constant(date_time=date_time, examReplyId=exam_reply_id, examId=exam_id,
                     teachingTaskId=teaching_task_id, exercises_id=exercises_id)
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
    return request(url, data).json()
    # assert 'optionsC' in r.json()


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
    for examStudentExerciseId, exerciseId, idx in assignment.exercises_id:
        json = xhr_question(date_time, exam_reply_id,  examStudentExerciseId, exerciseId)
        try:
            title, options_answers, category = json_extract(json)
            print(str(idx) + '.', title)
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
            save_answer(types, answer, data)

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
    hand_url = '/student/exam/manageExam.do?i%s&method=saveAnswer' % date()
    try:
        response = request(hand_url, data_copy)   # response "status": "ok"
    except requests.exceptions.ConnectionError:
        print('保存失败，请自行提交')
    else:
        print('保存成功')
        return response.json()    # AssertionError
