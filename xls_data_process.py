# encoding=utf-8
"""
@author: hxer
@contact: hxer7963@gmail.com
@time: 2017/4/26 17:49
"""
import os
import io
import re
import xlrd
from _warnings import warn
import time
from random import randint
from tkkc_common import get, session
from tkkc_headers import document_header


xlsx_directory = os.path.join(os.getcwd(), 'xlsx_directory')  # 平台无关，但可能用户下载之后不删除。。又打包发送出去


def mkdir_download():
    if not os.path.exists(xlsx_directory):
        os.mkdir(xlsx_directory)

def download_xls(course_name, xlsx_url):
    print('xlsx download url:', xlsx_url)
    download_is_true = False
    if os.path.exists(xlsx_directory):
        for file in os.listdir(xlsx_directory):   # tkkc_archive
            if not os.path.isdir(file) and file.startswith(course_name) and file.endswith('xls'):
                print('{}已下载'.format(file))
                download_is_true = True
                break
    if not download_is_true:
        download_page = get(xlsx_url, document_header).text
        resourceId_pattern = '"id":(.*?),"linkType"'
        resource = re.search(resourceId_pattern, download_page)
        resourceDownloadPermeters = 'data: "(.*?)&.*&taskId=(.*?)&iscomplete'
        postPermeters = re.search(resourceDownloadPermeters, download_page)
        print(postPermeters.group(1), postPermeters.group(2))
        download_url = 'http://tkkc.hfut.edu.cn/checkResourceDownload.do' #?{}'.format(postPermeters[1])
        data = {
            postPermeters[1]: None,
            'resourceId': resource.group(1),
            'downloadFrom': 1,
            'isMobile': 'false',
            'taskId': postPermeters[2],
            'iscomplete': 'true',
            'history': 'false'
        }
        print('{}.xls 正在下载...'.format(course_name))
        xls_resource = session.post(download_url, data, document_header)   # content字节码, stream=True
        print(xls_resource.status_code, xls_resource.text)
        print(xls_resource.json())
        if 'status' in xls_resource.json() and xls_resource.json()['status'] == 'indirect':  # 'status' in xls_resource.json and
            download_url = '/filePreviewServlet?indirect=true&resourceId={}'.format(resource.group(1))
            xls_resource = get(download_url, document_header)
        # # http://stackoverflow.com/questions/9419162/python-download-returned-zip-file-from-url
        try:
            from StringIO import StringIO
        except ImportError:
            from io import StringIO
        import rarfile, zipfile
        try:
            zf = zipfile.ZipFile(io.BytesIO(xls_resource.content))
            archive = zf
        except zipfile.error:
            try:
                rf = rarfile.RarFile(io.BytesIO(xls_resource.content))
                archive = rf
            except rarfile.error:
                raise TypeError("compress Type isn't zip nor rar!")
                exit(1)
        mkdir_download()
        for file in archive.namelist():
            if file.endswith('.xls'):
                print(file)
                archive.extract(file, path=xlsx_directory)
                if file is not course_name:
                    os.rename(r'{}/{}'.format(xlsx_directory, file), r'{}/{}.xls'.format(xlsx_directory, course_name))
                    import shutil
                    shutil.rmtree(os.path.join(xlsx_directory, file.split('/')[0]))
                print(file, 'download success!')


def question_extract(course_name, resource_url, discuss_cnt):
    download_xls(course_name, resource_url)
    xls = xlrd.open_workbook('{}/{}.xls'.format(xlsx_directory, course_name))
    questions_list = []
    sheet = xls.sheet_by_name('单选题')
    rows = sheet.nrows
    for index in range(discuss_cnt):
        random_index = randint(2, rows)
        question = sheet.row(random_index)[0].value.strip().replace(' ', '')
        if question[-1] == '。':
            question = question[:-1] + '？'
        if question.endswith('（）？'):
            question = question.replace('（）', '')
        else:
            answer = sheet.row(random_index)[-1].value
            index = ord(answer) - ord('A')
            answer = sheet.row(random_index)[2 + index].value
            question.replace('（）', answer)

        questions_list.append(question)
    return questions_list


def json_extract(count, json):
    types = json['type']
    options_answers = []
    for keys in json.keys():  # 'optionsA: 正确', 'optionsB: 错误'
        if keys.startswith('opt') and len(keys) == 8 and json[keys]:
            content = data_clear(json[keys])
            options_answers.append(content)
    title = data_clear(json['title'])
    if types == 1:
        category = '单选题'
    elif types == 4:
        category = '多选题'
    elif types == 2:
        category = '判断题'
    else:
        raise ValueError('主观题23333...')
    print('{}.{}'.format(count, title))
    return title, options_answers, category

specify_answers = ['中国化', '1', '60', '1300', '政治建设', '绿色低碳循环发展', '和谐共生', '和平合作', '开放包容', '互学互鉴', '互利共赢', '高中阶段教育',
                   '节能环保产业', '清洁生产产业', '清洁能源产业', '社会主义核心价值观', '人民日益增长的美好生活需要和不平衡不充分的发展之间的矛盾', '完善和发展中国特色社会主义制度',
                   '推进国家治理体系和治理能力现代化', '第二', '八十', '八千多万', '基本法', '2018', '常态化', '580', '基本实现 全面建成', '党', '13', '人与自然和谐发展',
                   '生态宜居', '乡风文明', '治理有效', '新时代', '自治', '法治', '德治', '维护国家安全', '教育强国', '人大协商', '人民团体协商', '社会组织协商', '个人主义',
                   '分散主义', '自由主义', '本位主义', '好人主义', '传统安全', '非传统安全', '国际公共产品', '三分之一', '组织力', '互利共赢', '和谐包容', '市场运作', '平衡和 可持续',
                   '有理想', '有本领', '有担当', '幸福家园', '爱心助困', '康复助医']

def xls_search_answer(title, options_answers, sheet_name, course_name):
    try:
        xls = xlrd.open_workbook('{}/{}.xls'.format(xlsx_directory, course_name))
    except FileNotFoundError as fnf:
        print('No such file or directory: {}/{}.xls'.format(xlsx_directory, course_name))
        exit()
    sheet = xls.sheet_by_name(sheet_name)
    rows = sheet.nrows
    answers_list = []
    for row in range(rows):
        row_question = data_clear(str(sheet.row(row)[0].value))
        if title in row_question:
            answers = sheet.row(row)[-1].value.split(',')
            if sheet_name == '判断题':
                answers_list.append('A' if answers[0] == '正确' else 'B')
            else:   # 将比对答案改为直接复制，认为xlsx题库的答案顺序与题给答案顺序一致
                answers_list = answers
    if not answers_list:
        if sheet_name == '判断题':
            if '270' in title:
                answers_list.append('A')
            elif '政府负责' in title or '没有任何改变' in title or '战胜自然' in title or '人民日益增长的美好生活需要与落后的社会生产之间的矛盾' in title:
                answers_list.append('B')
        else:
            for option in options_answers:
                if option in specify_answers:
                    answers_list.append(chr(options_answers.index(option)+ord('A')))

    if (sheet_name != '多选题' and len(answers_list) > 1) or (not answers_list) or (sheet_name == '多选题' and len(answers_list) < 2):
        # print(title, options_answers)       # 输出没有找到答案的题目与选项
        raise ValueError('没有找到答案')
    print('答案为: {}'.format(' '.join(answers_list)))
    return answers_list


def data_clear(titles):
    # 将题目/答案中的中文英文括号、中文句号，空格全部去除, 转码出现\xa0 和 \u3000应该用正则去除
    data_cleared = re.sub('（|）|。|\n|(\xa0)|(\u3000)|(\u2022)|\(|\)|(&nbsp;)|“|”', '', titles).strip().replace(' ', '')
    return data_cleared


def delete_xlsx(course_name=None):
    if os.path.exists(xlsx_directory):
        import shutil
        if course_name is None:
            if os.listdir(xlsx_directory):
                print('xlsx_directory目录已删除')
                shutil.rmtree(xlsx_directory)
        else:
            for file in os.listdir(xlsx_directory):
                file = os.path.join(xlsx_directory, file)
                if file.startswith(course_name):
                    if os.path.isdir(file):
                        shutil.rmtree(file)
                    else:
                        os.remove(file)
                print('{}已删除~'.format(file))

# if types == 1: '单选题'
# elif types == 4: '多选题'
# elif types == 2: '判断题'

if __name__ == '__main__':
    json = {"optionsA": "《关于打赢脱贫攻坚战的决定》",
            "optionsB": "《关于创新机制扎实推进农村扶贫开发工作的意见》",
            "optionsC": "《扶贫开发建档立卡工作方案》",
            "optionsD": "《关于创新机制扎实推进农村扶贫开发工作的意见》",
            "optionsE": "平衡和 可持续",
            "title": "2014年1月，中共中央办公厅、国务院办公厅印发( )，提出建立精准扶贫工作机制，要求对每个贫困村和贫困户建档立卡，逐村逐户制定帮扶措施，真扶贫、扶真贫，使他们在规定时间内达到稳定脱贫的目标。",
            "type": 1}
    title, options_answers, category = json_extract(1, json)
    print(options_answers)
    answers = xls_search_answer(title, options_answers, category, '形势与政策')
