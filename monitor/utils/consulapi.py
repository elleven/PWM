# -*- coding:utf-8 -*-
#Author:chao Yan

from django.conf import settings
import consul
from mgmt import models

class ConsulApi(object):
    def __init__(self):
        self.ip = settings.CONSUL_IP
        self.port = settings.CONSUL_PORT
        self.c = consul.Consul(host=self.ip,port=self.port,scheme='http')

    def get_kv(self,key):
        index,data = self.c.kv.get(key)
        return data['Value']

    def put_kv(self,path,value):
        return self.c.kv.put(path,value)

    def delete_kv(self,path,recurse=None):
        return self.c.kv.delete(path,recurse=recurse)

    def service_register(self, server_name, ip, port,tags):
        print ip,type(port)
        check = consul.Check.tcp(ip, int(port), "10s")  # 健康检查的ip，端口，检查时间
        # server_name后面的参数是id
        self.c.agent.service.register(server_name, "{}:{}".format(ip, port),
                                      address=ip, port=int(port), check=check, tags=[tags])  # 注册服务部分
        print("注册服务{server_name}成功")

    def service_unregister(self, ip, port):
        # 删除的是id
        self.c.agent.service.deregister('{}:{}'.format(ip, int(port)))

    def service_check(self):
        return self.c.agent.checks()

    def serializers_service_check(self):
        info = self.service_check()
        return info

    def service_check_serializers(self):
        info = self.serializers_service_check()
        dict1 = {}
        dict1["name"] = "online"
        dict1["value"] = 0
        dict2 = {}
        dict2["name"] = "offline"
        dict2["value"] = 0
        for key,value in info.items():
            status = value["Status"]
            if status == "passing":
                dict1["value"] += 1
            elif status == "critical":
                dict2["value"] += 1
        list1 = []
        list1.append(dict1)
        list1.append(dict2)
        return list1


class AlterToConsul(object):
    def __init__(self,rules_name,group):
        self.manager_type = settings.CONSUL_ALERTMANAGER_DIR
        self.path = "%s/%s/%s" % (self.manager_type,
                                  rules_name,
                               group)
        self.c = ConsulApi()

    def add_mode(self,mode):
        self.c.put_kv("%s/mode" % self.path,mode)

    def add_reslove(self,reslove):
        self.c.put_kv("%s/reslove" % self.path, reslove)

    def add_repeat(self,repeat):
        self.c.put_kv("%s/repeat" % self.path, repeat)

    def add_alert(self,dict1):
        self.add_mode(dict1["monitor_mode"])
        self.add_repeat(dict1["repeat_time"])
        self.add_reslove(dict1["resolve"])

    def del_alert(self):
        self.c.delete_kv(self.path,recurse=True)

class PromToConsul():
    def __init__(self,app_group,rules_name):
        self.manager_type = settings.CONSUL_PROMETHEUS_RULES_DIR
        self.path = "%s/%s/%s/%s" % (self.manager_type,
                                  app_group + ".yml",
                                  app_group + ".rules",
                                  rules_name)
        self.c = ConsulApi()

    def add_expr(self,expr):
        return self.c.put_kv("%s/expr" % self.path,expr)

    def add_for(self,long_time):
        return self.c.put_kv("%s/for" % self.path, long_time)

    def add_annotations_description(self,desc):
        return self.c.put_kv("%s/annotations/description" % self.path, "\"" + desc + "\"")

    def add_annotations_summary(self,summary):
        return self.c.put_kv("%s/annotations/summary" % self.path, "\"" + summary + "\"")

    def add_level(self,level):
        return self.c.put_kv("%s/labels/serverity" % self.path, level)

    def add_group(self,group):

        return self.c.put_kv("%s/labels/team" % self.path, group)

    def add_rules(self,dict1):
        self.add_expr(dict1["expr"])
        self.add_for(dict1["long_time"])
        self.add_annotations_description(dict1["desc"])
        self.add_annotations_summary(dict1["summary"])
        self.add_level(dict1["mysql_file_montior_info"])
        title_name = models.Role.objects.filter(pk=dict1["group"]).first().title + "_" + dict1["rules_name"]
        self.add_group(title_name)

    def del_rules(self):
        self.c.delete_kv(self.path,recurse=True)


c = ConsulApi()