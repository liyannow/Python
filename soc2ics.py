#coding=utf-8
# name:爬取教务系统的课程数据并写入到ICS文件中
# version:0.9
# author：eno17
# date:2016-10-29
# by python
# 操作：需要手动输入自己的验证码
# 功能：爬取教务系统的课程数据并写入到ICS文件中
# 其他：这次代码的完成 关于实现登录教务系统相关功能 极大地参考了 http://blog.csdn.net/qq_22222499/article/details/52664110 这位哥们的代码~

import os
import datetime
from lxml import etree
import requests
from urllib import quote

#用来爬取保存在字典中，并提供写入TXT文件的方法
class Spider_SOC:# SOC：Schedule of Classes
    def __init__(self):
        self.studentnumber = ""#学号
        self.password = "" #密码
        self.xsxm = ""
        self.url = "http://i.nbut.edu.cn:8016//default2.aspx"  # 教务系统网址
        self.imgUrl = "http://i.nbut.edu.cn:8016//CheckCode.aspx?" # 验证码的地址
        self.kcbdict = dict()  # 用来返回字典的值
        self.s = requests.session() # 用来保存状态

    def start_Spider(self):
        self.login_jwxt()  # 登录教务管理系统
        self.soc_Spider()  # 爬取个人课表的选课信息

    def outofdict(self):  # 接口 用来输出已经保存的字典
        return self.kcbdict

    def login_jwxt(self):
        # 第一步登录教务系统

        # 为了登录 需要构造POST数据
        # 需要_学号 密码 _VIEWSTATE的值  验证码


        # 学号 密码
        studentnumber = self.studentnumber
        password = self.password


        #获取__VIEWSTATE的值
        s = requests.session()
        url = self.url
        response = s.get(url)
        selector = etree.HTML(response.content)
        __VIEWSTATE = selector.xpath('//*[@id="form1"]/input/@value')[0]



        # 获取验证码并下载到本地以便手动输入

        imgUrl = self.imgUrl
        imgresponse = s.get(imgUrl, stream=True)
        print s.cookies
        image = imgresponse.content
        DstDir = os.getcwd() + os.sep
        print("保存验证码到：" + DstDir + "code.jpg" + "\n")
        try:
            with open(DstDir + "code.jpg", "wb") as jpg:
                jpg.write(image)
        except IOError:
            print("IO Error\n")
        finally:
            jpg.close
        # 手动输入验证码
        code = raw_input("验证码是(验证码在同级目录下)")


        # 构建post数据
        data = {
            "__VIEWSTATE": __VIEWSTATE,
            "txtUserName": studentnumber,
            "TextBox2": password,
            "txtSecretCode": code,
            "Button1": "",
        }

        # 提交表头，里面的参数是电脑各浏览器的信息。模拟成是浏览器去访问网页。
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36",
        }


        # 登陆教务系统
        response = s.post(self.url, data=data, headers=headers)



        # 获取学生基本信息

        content = response.content.decode('gb2312')  # 网页源码是gb2312要先解码
        selector = etree.HTML(content)
        try:
            text = selector.xpath('//*[@id="xhxm"]/text()')[0]
            text = text.replace(" ", "")
        except:
            print '可能是验证码输入错误'

        print '欢迎',
        print text
        xsxm = text[:len(text) - 2]

        # 保存名字待会有用的
        self.xsxm = xsxm

        # 保存状态
        self.s = s

    def soc_Spider(self):

        # 获取个人选课信息

        grxkurl = "http://i.nbut.edu.cn:8016//xsxkqk.aspx?xh=" + self.studentnumber + "&xm=%" + quote(
            self.xsxm.encode('gb2312')) + "%FC&gnmkdm=N121603"
        headers = {
            "Referer": "http://i.nbut.edu.cn:8016//xs_main.aspx?xh=" + self.studentnumber,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
        }
        response = self.s.get(grxkurl, headers=headers)
        # html代表访问课表页面返回的结果就是课表。下面做的就是解析这个html页面。
        html = response.content.decode("gb2312")
        selector = etree.HTML(html)

        # 以单个课为单位 匹配N个选课信息
        content = selector.xpath('//*[@class = "datelist "]/tr[not (@class = "datelisthead")]')


        # kcb 用来临时存储每节课的信息
        kcb = list()

        for each in content:
            for line in each:
                kcb.append(line.text)
                for son in line:
                    kcb.append(son.text)

        # 用来存储选课信息，以选课名称为键，时间，地点，老师名字组成的字典为值
        kcbdict = {}

        for i in range(len(kcb) / 20):
            valuedict = {} # 临时存放的字典

            valuedict.setdefault('time', kcb[i * 20 + 11]) # 时间
            valuedict.setdefault('teachername', kcb[i * 20 + 7]) # 老师名字
            valuedict.setdefault('place', kcb[i * 20 + 12]) # 地点
            kcbdict.setdefault(kcb[i * 20 + 3], valuedict) # 把字典放入值中


        self.kcbdict =  kcbdict # 保存到类属性里面去 用来输出


class SOC_Process(): # 用来转化为ICS格式的文件
    def __init__(self,dict):
        # 设置开学第1周的 星期一
        self.sst = datetime.datetime(2016, 9, 5) #开学起始日期

        self.kcbdict = dict # 将字典存进类中
        self.starttime = { # 上课起始时间
            1: '080000',
            2: '085500',
            3: '100000',
            4: '105500',
            5: '133000',
            6: '142500',
            7: '152000',
            8: '161500',
            9: '180000',
            10: '185500',
            11: '194000'
        }

        self.endtime = { # 下课时间
            1: '084500',
            2: '094000',
            3: '104500',
            4: '114000',
            5: '141500',
            6: '151000',
            7: '160500',
            8: '170000',
            9: '184500',
            10: '193000',
            11: '202500'
        }

        self.day2num = { # 判断从开学的哪天起上课
            u'周一': 0,
            u'周二': 1,
            u'周三': 2,
            u'周四': 3,
            u'周五': 4,
            u'周六': 5,
            u'周日': 6

        }

        self.day2en = {  # 只在'周X'上课
            u'周一': 'MO',
            u'周二': 'TU',
            u'周三': 'WE',
            u'周四': 'TH',
            u'周五': 'FR',
            u'周六': 'SA',
            u'周日': 'SU'

        }


    def start_process(self):
        self.write_process()


    def write_process(self): # 开始处理并写入
        kcbdict = self.kcbdict
        # 打开iCal文件
        # 写入日历的头部文件
        global f
        f = open("课程表.ics", "w")
        contenthead = '''BEGIN:VCALENDAR
PRODID:-//Google Inc//Google Calendar 70.9054//EN
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:课程表
X-WR-TIMEZONE:Asia/Shanghai
BEGIN:VTIMEZONE
TZID:Asia/Shanghai
X-LIC-LOCATION:Asia/Shanghai
BEGIN:STANDARD
TZOFFSETFROM:+0800
TZOFFSETTO:+0800
TZNAME:CST
DTSTART:19700101T000000
END:STANDARD
END:VTIMEZONE
'''
        f.write(contenthead)

        # 遍历字典
        for key in kcbdict.keys():

            # 首先分割
            # 网络课 还有 课程设计师没有上课时间的 过滤掉
            if kcbdict[key]['time'] is None:
                continue

            # 单双周及调课及三节课的处理
            timelist = kcbdict[key]['time'].split(';')
            placelist = kcbdict[key]['place'].split(';')

            # 单双周及调课及三节课的处理后的循环
            for i in range(len(placelist)):
                f.write(self.one_write_process(key, kcbdict[key]['teachername'], timelist[i], placelist[i], i))  # i 就是来区分UID

                # 进行处理
                # 再调入 进行单个写入事件处理
                # 写入


        #写入尾部 完成
        contentlast = '''END:VCALENDAR'''
        f.write(contentlast)
        f.close()  # 关闭文件
        print '写入成功，请查找同级目录下的 课程表.ics文件'

    def one_write_process(self,name,teachername,time,place,flag): # name 课程名称 teachername 老师名字 time 完整的时间约束 place 地点 flag 区分UID的
        day = time[:2] # 获取周X上课
        sst = datetime.datetime(2016, 9, 5) # 这个是起始上课日期
        sst = self.sst


        # 获取开始上课的周数
        startnum = datetime.timedelta(weeks=int(time[time.rfind('第'.decode('utf8')) + 1:time.rfind('-')]) - 1)

        # 选课开始上课的日期
        startdate = sst + datetime.timedelta(
            weeks=int(time[time.rfind('第'.decode('utf8')) + 1:time.rfind('-')]) - 1) + datetime.timedelta(
            days=self.day2num[day])


        # startdate enddate 只是上课 下课时间不同 日期是一样的
        enddate = startdate


        # 获取上课具体是哪几节
        classsstr = time[time.find('第'.decode('utf8')) + 1:time.find('节'.decode('utf8'))]
        classstart = classsstr.split(',')[0]
        classend = classsstr.split(',')[len(classsstr.split(',')) - 1]


        # 开始日期 及 时间
        startdate = startdate.strftime("%Y%m%d") + 'T' + self.starttime[int(classstart)]  # *7+开学日期 + 7 + 上课时间

        # 结束日期 及 时间
        enddate = enddate.strftime("%Y%m%d") + 'T' + self.endtime[int(classend)]  # *7 +开学日期 + 下课时间
        # startdate = #开学第一天+ 上课时间 #第节中 第一个 + 第周中第一个 - 1 *7
        # enddate = calstr #开学第一天 + 下课时间 第节中 最后一个+ 第周中第一个 -1 *7

        # 用来循环的 截止日期及时间
        untildate = ((sst + datetime.timedelta(
            weeks=int(time[time.rfind('-') + 1:time.rfind('周'.decode('utf8'))]) - 1) + datetime.timedelta(
            days=4)).strftime("%Y%m%d") + 'T' + '235900Z;')

        # 如果有单双周的限制 再 写入
        if len(time.split('|')) == 2:
            untildate += 'INTERVAL = 2;'  # 单双周的限制


# iCal文件 单个事件的格式
        writecontent = '''BEGIN:VEVENT
DTSTART;TZID=Asia/Shanghai:''' + startdate + '''
DTEND;TZID=Asia/Shanghai:''' + enddate + '''
RRULE:FREQ=WEEKLY;WKST=SU;UNTIL=''' + untildate + '''BYDAY=''' + self.day2en[day] + '''
DTSTAMP:''' + str(datetime.datetime.today().strftime("%Y%m%d")) + 'T000000Z' + '''
UID:''' + name.encode('utf8') + str(flag) + '''
CREATED:''' + str(datetime.datetime.today().strftime("%Y%m%d")) + 'T000000Z' + '''
DESCRIPTION:''' + teachername.encode('utf8') + '''
LAST-MODIFIED:''' + str(datetime.datetime.today().strftime("%Y%m%d")) + 'T000000Z' + '''
LOCATION:''' + place.encode('utf8') + '''
SEQUENCE:0
STATUS:CONFIRMED
SUMMARY:''' + name.encode('utf8') + '''
TRANSP:OPAQUE
X-APPLE-TRAVEL-ADVISORY-BEHAVIOR:AUTOMATIC
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:This is an event reminder
TRIGGER:-P0DT0H20M0S
END:VEVENT

'''
        return writecontent # 返回



if __name__ == '__main__':
    spider = Spider_SOC()
    spider.start_Spider()
    procss = SOC_Process(spider.outofdict())
    procss.start_process()