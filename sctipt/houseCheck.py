import requests
import json
import time
import datetime
import schedule
import traceback
from apscheduler.schedulers.blocking import BlockingScheduler
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header

###########################################################
#成都买房摇号查询脚本
#每天查询一次，邮件发送查询结果
#需要设置：
# 1. 发件邮箱信息
# 2. 查询时间
###########################################################
# 用于构建邮件头
# 发信方的信息：发信邮箱，QQ 邮箱授权码
from_addr = ''
password = ''

# 收信方邮箱
to_addr = ''

# 发信服务器
smtp_server = 'smtp.qq.com'

# 发信时间
hour = 0
minute = 1

# 查询地址
houseURL = "https://zw.cdzj.chengdu.gov.cn/lottery/accept/projectList"
############################################################

class HouseChecker:
    def __init__(self):
        self.enrolling = 0
        self.htmlBody = ""
        self.htmlTable = ""
        self.projectHTMLTable = ""
        self.projectList = []
        self.session = requests.session()
        self.houseURL = houseURL
        self.headers = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36"
        }

    def fetchHTML(self):
        try:
            response = self.session.get(url=self.houseURL,
                                        headers=self.headers)
            if response.status_code == 200:
                self.htmlBody = response.text
                return True
            else:
                return False
        except Exception as e:
            return False, e

    def parseData(self):
        soap = BeautifulSoup(self.htmlBody, "html.parser")
        self.htmlTable = soap.find_all("table")[1]
        self.htmlTable[
            "style"] = 'padding-bottom: 30px; text-align: center; color: rgb(51, 51, 51); font-family: "Microsoft Yahei", "Segoe UI", "Hiragino Sans GB", "WenQuanYi Micro Hei", Arial, Simsun, sans-serif; font-size: 14px;'
        self.projectHTMLTable = soap.find('tbody', id='_projectInfo')

        self.projectList = []  #Resest List
        self.enrolling = 0  #Reset Enrolling
        for projectHTML in self.projectHTMLTable.contents:
            try:
                attrList = projectHTML.find_all('td')
                houseAttr = {
                    "区域": attrList[2].text,
                    "项目名称": attrList[3].text,
                    "预售证号": attrList[4].text,
                    "预售范围": attrList[5].text,
                    "住房套数": attrList[6].text,
                    "咨询电话": attrList[7].text,
                    "登记开始时间": attrList[8].text,
                    "登记结束时间": attrList[9].text,
                    "项目报名状态": attrList[11].text
                }
                if (houseAttr["项目报名状态"] == "正在报名"):
                    self.enrolling += 1
                self.projectList.append(houseAttr)
            except:
                pass

    def sendMail(self):
        urlBanner = "<div style=\"text-align: center;\"><a href=\"https://zw.cdzj.chengdu.gov.cn/lottery/accept/projectList\">https://zw.cdzj.chengdu.gov.cn/lottery/accept/projectList</a><br></div>"
        try:
            # 邮箱正文内容，第一个参数为内容，第二个参数为格式(plain 为纯文本)，第三个参数为编码
            msg = MIMEText(urlBanner + str(self.htmlTable), 'html', 'utf-8')
            # 邮件头信息
            # msg['From'] = Header(from_addr)
            now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            msg['From'] = Header(u'from Mark<{}>'.format(from_addr), 'utf-8')
            msg['To'] = Header(to_addr)
            msg['Subject'] = Header(
                now + " 今日摇号检测-正在报名: " + str(self.enrolling) + " 个", 'utf-8')
            # 开启发信服务，这里使用的是加密传输
            server = smtplib.SMTP_SSL(host=smtp_server)
            server.connect(smtp_server, 465)
            # 登录发信邮箱
            server.login(from_addr, password)
            # 发送邮件
            server.sendmail(from_addr, to_addr, msg.as_string())
            # 关闭服务器
            server.quit()
        except Exception as e:
            print(traceback.format_exc())

    def process(self):
        self.fetchHTML()
        self.parseData()
        self.sendMail()
        print(
            str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + " " +
            str(self.enrolling) + " 个项目正在报名 今日查询结果已发送")


if __name__ == "__main__":
    checker = HouseChecker()
    print("开始定时任务，每天{:02d}:{:02d}查询房源".format(hour, minute))
    scheduler = BlockingScheduler()
    scheduler.add_job(checker.process,
                      'cron',
                      hour=hour,
                      minute=minute,
                      misfire_grace_time=900)
    scheduler.start()