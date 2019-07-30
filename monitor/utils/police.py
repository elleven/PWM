# -*- coding:utf-8 -*-
#Author:chao Yan

import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from mgmt import models
from django.conf import settings
from monitor import models as m
from monitor.utils.tools import r
import time

class Police(object):
    def __init__(self,group):
        self.group = group
        self.get_group_info()
        self.msg = ""
        self.level = ""
        self.status = ""
        self.alertname = ""

    def get_group_info(self):
        role_obj = models.Role.objects.get(title=self.group)
        self.user_obj_list = role_obj.group.all()

    def record_police(self,level,rules_name,resolve_status,msg):
        """
        记录报警记录
        :return:
        """
        m_obj = m.Rules.objects.filter(rules_name=rules_name).first()
        m.MsgNotitfy.objects.update_or_create(rules=m_obj, defaults={
            "level":level,
            "monitor_level_choices":resolve_status,
            "msg":msg
        })

    def del_police(self,rules_name):
        """
        当报警修复的时候，把此报警的数据，从MsgNotitfy表删除,从redis中删除报警次数
        :param rules_name:
        :return:
        """
        m_obj = m.Rules.objects.filter(rules_name=rules_name).first()
        objs = m.MsgNotitfy.objects.filter(rules=m_obj).first()
        dict1 = {}
        dict1["level"] = objs.level
        dict1["rules"] = objs.rules
        dict1["monitor_level_choices"] = objs.monitor_level_choices
        dict1["create_timestamp"] = objs.create_timestamp
        dict1["last_edit_timestamp"] = objs.last_edit_timestamp
        dict1["msg"] = objs.msg
        key_name = "error_" + str(objs.rules.id)
        dict1["repeat_num"] = int(r.get_inc(key_name))
        m.HisMsgNotitfy.objects.create(**dict1)
        objs.delete()


    def record_his_police(self,objs):
        """
        记录报警历史记录，如果报警解除，把数据插入到历史表中
        :return:
        """
        # m_obj = m.Rules.objects.filter(rules_name=rules_name).first()
        dict1 = {}
        dict1["level"] = objs.level
        dict1["rules"] = objs.rules
        dict1["monitor_level_choices"] = objs.monitor_level_choices
        dict1["create_timestamp"] = objs.create_timestamp
        dict1["last_edit_timestamp"] = objs.last_edit_timestamp
        dict1["msg"] = objs.msg
        key_name = "error_" + str(objs.rules.id)
        dict1["repeat_num"] = int(r.r_inc(key_name))
        m.HisMsgNotitfy.objects.create(**dict1)

    def get_msg(self,data):
        # msg = ""
        for i in data:
            if i["status"] == 'firing':
                # if level == 'firing' or level == 'resolved':
                self.msg += "问题" + i["annotations"]["description"] + "\n"
                self.level = i['labels']['serverity']
                self.alertname = i['labels']['alertname']
                self.status = i['status']
            elif i["status"] == 'resolved' and self.status != 'firing':
                self.status = 'resolved'
                self.alertname = i['labels']['alertname']
                self.msg += "已解决" + i["annotations"]["description"] + "\n"
        if self.status == "resolved":
            pass
            # self.del_police(self.alertname)
        else:
            print "iiiiii"
            self.record_police(self.level, self.alertname, self.status, self.msg)


    def sms(self,data):
        # msg = ""
        # for i in data:
        #     level = i['labels']['serverity']
        #     print "lllllllllllllll",level
        #     if i['status'] == 'firing' or i['status'] == 'resolved':
        #         msg += i["annotations"]["description"] + "\n"
        #         # level = i['labels']['serverity']
        #         alertname = i['labels']['alertname']
        #         status = i['status']
        # if status == "resolved":
        #     self.del_police(alertname)
        #     # self.record_his_police(level,alertname,status,msg)
        # else:
        #     print "ssdgfdgfgdfg"
        #     self.record_police(level,alertname,status,msg)
        # self.get_msg(data)
        print "mmmm"
        url = settings.SMS_URL
        for i in self.user_obj_list:
            body = {"sysCode": "JYECS", "orgCode": "", "messageType": "", "phone": i.phone,
                "message": "【云计算】【%s】等级:【%s】报警内容: %s" % (self.status, self.level, self.msg)}
            headers = {'content-type': "application/json"}
            response = requests.post(url, data=json.dumps(body), headers=headers)
            response.text
        return "ok"

    def sendmail(self,data):
        print "ssss"
        smtpServer = settings.SENDMAIL_SMTP
        sender = settings.SENDMAIL_SENDER
        password = settings.SENDMAIL_SENDER_PASSWORD
        # for i in self.user_obj_list:
        #     print i.email
        to_list = [x.email for x in self.user_obj_list]
        print "yttttt", to_list
        # msg = ""
        # for i in data:
        #     # if level == 'firing' or level == 'resolved':
        #     msg += i["annotations"]["description"] + "\n"
        #     level = i['labels']['serverity']
        #     alertname = i['labels']['alertname']
        #     status = i['status']
        # if status == "resolved":
        #     print "ooooooo"
        #     self.del_police(alertname)
        # else:
        #     print "iiiiiii"
        #     self.record_police(level,alertname,status,msg)
        # self.get_msg(data)
        smtpObj = smtplib.SMTP(smtpServer)
        msg = MIMEText(self.msg, _charset='utf-8')
        msg['Subject'] = '[%s]prometheus报警 级别:%s' % (self.status,self.level)
        # msg['From'] = me
        msg['From'] = sender
        msg['To'] = ";".join(to_list)
        smtpObj.login(sender,password)
        smtpObj.sendmail(sender, to_list, msg.as_string())
        return 'ok'

    def wx(self,data):
        to_list = [str(x.wx_id) for x in self.user_obj_list]
        t = time.time()
        t4 = time.localtime(t)
        time1 = time.strftime("%Y-%m-%d %H:%M:%S", t4)
        print "ttt", to_list
        headers = {}
        headers['Content-Type'] = 'application/json'
        data = {
            "sysCode": "weChat",
            "funcType": "weChat",
            "funcPointType": "skynetEarlyWarning",
            "frontTransNo": "Q1001F3D7BB211111afgdsafs1",
            "frontTransTime": time1,
            "interfaceNo": "skynetEarlyWarning",
            "prod": "weChat",
            "moduleData": {},
            "interfaceData": {
              "skynetEarlyWarning": {
                "tousers": to_list,
                "content": "【云计算】【%s】等级:【%s】报警内容: %s" % (self.status, self.level, self.msg),
                "isInvoking": "1"
              }
            }
        }
        r = requests.post(settings.WX_URL, headers=headers,data=json.dumps(data),verify=False)
        return 'ok'