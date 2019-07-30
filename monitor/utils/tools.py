# -*- coding:utf-8 -*-
#Author:chao Yan

from monitor.utils.consulapi import *
from monitor import models
from django.apps import apps
import redis
from django.conf import settings
import time
import requests
import json
import datetime


class RedisClass(object):
    def __init__(self):
        self.r = redis.Redis(host=settings.MONTIOR_REDIS, port=settings.MONTIOR_PORT)

    def r_inc(self, key):
        self.r.incr(key, amount=1)

    def get_inc(self,key):
        return self.r.get(key)

    def del_inc(self,key):
        self.r.delete(key)

    def set_inc(self,key,value):
        self.r.set(key,value)

    def mv_inc(self,key):
        old_inc = "error_" + key.split("_")[0]
        print "oooooooo",old_inc
        value = self.get_inc(old_inc)
        print "vvvvvvvv",value
        self.set_inc(key,value)

r = RedisClass()

def get_today_time_format():
    t = time.time()
    t4 = time.localtime(t)
    return time.strftime("%Y-%m-%d", t4)

def getmodelfield(appname,modelname,field_name):
    """
    获取model的verbose_name和name的字段
    """
    modelobj = apps.get_model(appname, modelname)
    filed = modelobj._meta.fields

    fielddic = {}
    #
    params = [f for f in filed if f.name in field_name]
    for i in params:
        fielddic[i.name] = i.verbose_name
    return fielddic


def get_rules_info(obj,list1,field_name):
    include = [field_name]
    name = getmodelfield("monitor", "Rules", include)
    dict4 = dict(label=name[field_name],children=[])
    dict5 = {}
    dict5["label"] = getattr(obj,field_name)
    dict4["children"].append(dict5)
    list1.append(dict4)


def get_tree():
    """
    获取数据源的服务树
    :return:
    """
    list1 = []
    for i in models.Job.objects.all():
        dict1 = {}
        dict1["label"] = i.job_name
        dict1["children"] = []
        dict_target = {}
        dict_target["label"] = "数据源节点"
        dict_target["children"] = []
        for ii in i.tags.all():
            dict2 = {}
            dict2["label"] = ii.target_name
            dict_target["children"].append(dict2)
        dict1["children"].append(dict_target)
        dict_scrape = {}
        dict_scrape["label"] = "采集间隔"
        dict_scrape["children"] = []
        dict2 = {}
        dict2["label"] = i.scrape
        dict_scrape["children"].append(dict2)
        dict1["children"].append(dict_scrape)

        # dict2 = {}
        # try:
        #     dict2["label"] = i.app.application_name
        # except:
        #     continue
        # dict2["children"] = []
        # try:
        for iiii in i.app.all():
            dict2 = {}
            dict2["label"] = iiii.application_name
            dict2["children"] = []

            for iii in iiii.app_info.all():
                dict3 = {}
                dict3["label"] = iii.rules_name
                dict3["children"] = []

                dict4 = {}
                dict4["label"] = "组"
                dict4["children"] = []
                dict5 = {}
                dict5["label"] = iii.group.title
                dict4["children"].append(dict5)
                dict3["children"].append(dict4)

                get_rules_info(iii,dict3["children"], "expr")
                get_rules_info(iii, dict3["children"], "long_time")
                get_rules_info(iii, dict3["children"], "repeat_time")
                get_rules_info(iii, dict3["children"], "monitor_mode")
                get_rules_info(iii, dict3["children"], "resolve")
                get_rules_info(iii, dict3["children"], "summary")
                get_rules_info(iii, dict3["children"], "desc")

                dict2["children"].append(dict3)
            dict1["children"].append(dict2)
        # except:
        #     pass
        list1.append(dict1)
        include = ["expr"]
        # print getmodelfield("monitor", "Rules", include)
    return list1


class AlertmanagerSilence(object):
    url = settings.ALERTMANAGER_HTTP

    @staticmethod
    def time_change_utc(date):
        # print "dddddd",date
        d = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        t = d.timetuple()
        timeStamp = int(time.mktime(t))
        utc_st = datetime.datetime.utcfromtimestamp(timeStamp)
        return datetime.datetime.strftime(utc_st, '%Y-%m-%dT%H:%M:%SZ')

    @classmethod
    def add_slicence(cls, data):
        header = {"Content-Type": "application/json"}
        startsAt = cls.time_change_utc(data["startsAt"])
        data["startsAt"] = startsAt
        endsAt = cls.time_change_utc(data["endsAt"])
        data["endsAt"] = endsAt
        if data.has_key("id"):
            data.pop("id")
        data = json.dumps(data)
        r = requests.post(cls.url + settings.ALERTMANAGER_SILENCES_URI,data,headers=header)
        print r.text, type(r.text)
        return eval(r.text)["silenceID"]

    @classmethod
    def delete_slicence(cls, slicence_id):
        r = requests.delete(cls.url +  settings.ALERTMANAGER_SILENCES_DELETE_URI + '/' + slicence_id)
        print r.text





class MysqlToConsul(object):

    def to_create_prometheus_job(self):
        """
        从mysql同步到consul中的prometheus-job
        :return:
        """
        for i in models.Job.objects.all():
            c.put_kv("%s/%s/%s" % (settings.CONSUL_JOB_DIR,
                                   i.job_name,
                                   settings.CONSUL_IP + ":" + str(settings.CONSUL_PORT)),
                                i.scrape)

    def to_alertmanger_config(self):
        """
        从mysql同步到consul中的alertmanager-config
        :return:
        """
        for i in models.Rules.objects.all():
            a_obj = AlterToConsul(i.rules_name, i.group.title)
            dict1 = {}
            dict1["monitor_mode"] = i.monitor_mode
            dict1["repeat_time"] = i.repeat_time
            dict1["resolve"] = i.resolve
            a_obj.add_alert(dict1)

    def to_create_prometheus_rules(self):
        """
        从mysql同步到consul中的prometheus-rules
        :return:
        """
        for i in models.Rules.objects.all():
            p_obj = PromToConsul(i.application_info.application_name, i.rules_name)
            dict1 = {}
            dict1["expr"] = i.expr
            dict1["long_time"] = i.long_time
            dict1["desc"] = i.desc
            dict1["summary"] = i.summary
            dict1["mysql_file_montior_info"] = i.mysql_file_montior_info
            dict1["rules_name"] = i.rules_name
            dict1["group"] = i.group.id
            p_obj.add_rules(dict1)

    def mysql_to_consul_create(self):
        """
        整体同步
        :return:
        """
        self.to_create_prometheus_job()
        self.to_alertmanger_config()
        self.to_create_prometheus_rules()