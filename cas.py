# coding=utf8

import requests
from lxml import etree
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pandas import DataFrame

plt.rcParams['font.sans-serif'] = ['simhei']    # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

req = requests.get('http://www.cas.cn/tz/201708/t20170801_4610395.shtml')

body = req.text.encode('ISO-8859-1')
selector = etree.HTML(body)

department_dict = {'数学物理学': None, '化学': None, '生命科学和医学': None, '地学': None, '信息技术科学': None, '技术科学': None}
department_index = ['数学物理学', '化学', '生命科学和医学', '地学', '信息技术科学', '技术科学']

# 6个部门
for i in range(6):
    tbody_list = selector.xpath('//*[@id="cztxxb1x"]/div[1]/div/div/div/table[' + str(i + 1) + ']/tbody')[0]
    name_list = [line[1][0][0].text for line in tbody_list]
    age_list = [int(line[2][0][0].text) for line in tbody_list]
    major_list = [line[3][0][0].text for line in tbody_list]
    work_list = [line[4][0][0].text for line in tbody_list]

    data = {'name': name_list, 'age': age_list, 'major': major_list, 'work': work_list}
    department_dict[department_index[i]] = DataFrame(data)
    department_dict[department_index[i]][u'学部'] = department_index[i]

result = pd.concat([department_dict[line] for line in department_index])
grouped = result.groupby(result[u'学部'])

final = grouped['age'].min().to_frame().rename(columns={'age': u'最小年龄'})

final[u'平均年龄'] = grouped['age'].mean() - grouped['age'].min()
final[u'最小年龄'] = grouped['age'].min()
final[u'最大年龄'] = grouped['age'].max() - grouped['age'].mean()


result = pd.merge(min_frame, mean_frame, how='inner',on=u'学部')
final.plot(kind='bar', title=u'各学部年龄分布', stacked = True, alpha=0.5)

for i, value in enumerate(grouped['age'].mean()):
    plt.text(i - 0.1, int(value)+1, int(value))

for i, value in enumerate(grouped['age'].max()):
    plt.text(i - 0.1, int(value)+1, int(value))

for i, value in enumerate(grouped['age'].min()):
    plt.text(i - 0.1, int(value)+1, int(value))

plt.ylable = u'年龄'
plt.legend(loc='lower left')

plt.axhline(result['age'].mean(), color='r', linestyle='--')
plt.axhline(grouped['age'].min().mean(), color='r', linestyle='--')
plt.axhline(grouped['age'].max().mean(), color='r', linestyle='--')

plt.xticks(rotation=360)
plt.show()
