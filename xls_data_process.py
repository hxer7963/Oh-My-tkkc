# encoding=utf-8
"""
@author: hxer
@contact: hxer7963@gmail.com
@time: 2017/4/26 17:49
"""
import io, re
import xlrd
from request import request


def xls2dict(xls):
    """ param: xls -> a type of xlrd.open_workbook """
    sheets_name = ['单选题', '多选题', '判断题']
    from collections import defaultdict
    xls_dict = defaultdict(list)
    for sheet_name in sheets_name:
        try:
            sheet = xls.sheet_by_name(sheet_name)
        except xlrd.biffh.XLRDError:
            continue
        rows = sheet.nrows
        for row_no in range(rows):
            qst = data_clear(str(sheet.row(row_no)[0].value))
            answers = str(sheet.row(row_no)[-1].value).split(',')
            if sheet_name == '判断题':
                answers = ['A'] if answers[0].strip() == '正确' else ['B']
            xls_dict[hash(qst)] = answers
    return xls_dict


def excel_dict(xlsx_url):
    """ Download and extract zip/rar file in memory rather than a file in local disk """
    download_page = request(xlsx_url).text
    resourceId_pattern = '"id":(.*?),"linkType"'
    resource = re.search(resourceId_pattern, download_page)
    resourceDownloadPermeters = 'data: "(.*?)&.*&taskId=(.*?)&iscomplete'
    postPermeters = re.search(resourceDownloadPermeters, download_page)
    print('正在下载excel文件...')
    download_url = '/checkResourceDownload.do' #?{}'.format(postPermeters[1])
    data = {
        'MIME Type': 'application/x-www-form-urlencoded',
        postPermeters[1]: '',
        'resourceId': resource.group(1),
        'downloadFrom': 1,
        'isMobile': 'false',
        'taskId': postPermeters[2],
        'iscomplete': 'false',
        'history': 'false'
    }
    xls_resource = request(download_url, data)   # content字节码, stream=True
    # print(xls_resource.json())
    if 'status' in xls_resource.json() and xls_resource.json()['status'] == 'indirect':  # 'status' in xls_resource.json and
        download_url = '/filePreviewServlet?indirect=true&resourceId={}'.format(resource.group(1))
        xls_resource = request(download_url)
    print'资源下载成功，正在解压...')
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
    else:
        for file in archive.infolist():
            if file.filename.endswith('.xls'):
                with archive.open(file) as fd:
                    import xlrd
                    xls = xlrd.open_workbook(file_contents=fd.read())
                    return xls2dict(xls)


def json_extract(json):
    types, options_answers = json['type'], []
    for keys in json.keys():  # 'optionsA: 正确', 'optionsB: 错误'
        if keys.startswith('opt') and len(keys) == 8 and json[keys]:
            options_answers.append(data_clear(json[keys]))
    title = data_clear(json['title'])
    if types == 1:
        category = '单选题'
    elif types == 4:
        category = '多选题'
    elif types == 2:
        category = '判断题'
    else:
        raise ValueError('主观题23333...')
    return title, options_answers, category

specify_answers = {'中国化', '1', '60', '1300', '政治建设', '绿色低碳循环发展', '和谐共生', '和平合作', '开放包容', '互学互鉴', '互利共赢', '高中阶段教育',
                   '节能环保产业', '清洁生产产业', '清洁能源产业', '社会主义核心价值观', '人民日益增长的美好生活需要和不平衡不充分的发展之间的矛盾', '完善和发展中国特色社会主义制度',
                   '推进国家治理体系和治理能力现代化', '第二', '八十', '八千多万', '基本法', '2018', '常态化', '580', '基本实现 全面建成', '党', '13', '人与自然和谐发展',
                   '生态宜居', '乡风文明', '治理有效', '新时代', '自治', '法治', '德治', '维护国家安全', '教育强国', '人大协商', '人民团体协商', '社会组织协商', '个人主义',
                   '分散主义', '自由主义', '本位主义', '好人主义', '传统安全', '非传统安全', '国际公共产品', '三分之一', '组织力', '互利共赢', '和谐包容', '市场运作', '平衡和 可持续',
                   '有理想', '有本领', '有担当', '幸福家园', '爱心助困', '康复助医'}

def xls_search_answer(xls_dict, title, options_answers, sheet_name):
    title = data_clear(title)
    answers_list = xls_dict[hash(title)]
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
    return answers_list


def data_clear(titles):
    # 将题目/答案中的中文英文括号、中文句号，空格全部去除, 转码出现\xa0 和 \u3000应该用正则去除
    data_cleared = re.sub('（|）|。|\n|(\xa0)|(\u3000)|(\u2022)|\(|\)|(&nbsp;)|“|”', '', titles).strip().replace(' ', '')
    return data_cleared


if __name__ == '__main__':
    json = {"optionsA": "《关于打赢脱贫攻坚战的决定》",
            "optionsB": "《关于创新机制扎实推进农村扶贫开发工作的意见》",
            "optionsC": "《扶贫开发建档立卡工作方案》",
            "optionsD": "《关于创新机制扎实推进农村扶贫开发工作的意见》",
            "optionsE": "平衡和 可持续",
            "title": "2014年1月，中共中央办公厅、国务院办公厅印发( )，提出建立精准扶贫工作机制，要求对每个贫困村和贫困户建档立卡，逐村逐户制定帮扶措施，真扶贫、扶真贫，使他们在规定时间内达到稳定脱贫的目标。",
            "type": 1}
    title, options_answers, category = json_extract(json)
    # print(options_answers)
    # answers = xls_search_answer(title, options_answers, category, '形势与政策')
    xls = xlrd.open_workbook('/Users/hexin/Downloads/形势与政策学习资料20180319/形势与政策题库.xls')
    xls_dict = xls2dict(xls)
    xls_search_answer(xls_dict, '初步核算，我国2016年国内生产总值比2015年增长（ ）。', options_answers, '单选题')
