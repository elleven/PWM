# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import unicode_literals

from monitor.app_serializers import *
from rest_framework.response import Response
from rest_framework import viewsets, mixins
from monitor import models
from mgmt.utils.c_pagination import CPageNumberPagination
from rest_framework import filters
from rest_framework import status
from monitor.utils.consulapi import c
from django.conf import settings
from rest_framework.decorators import list_route
from mgmt.utils.model_choices import choices
from monitor.utils.consulapi import PromToConsul
from monitor.utils.consulapi import AlterToConsul
from mgmt import models as mm
import json
from monitor.utils.police import Police
from monitor.utils.tools import get_tree
from django.http import HttpResponse, StreamingHttpResponse,JsonResponse
from django.db import transaction
from rest_framework.views import APIView
from mgmt.utils.response_result import BaseResponse
from monitor.utils.tools import *

from django.db.models.signals import (post_delete, post_save)
from django.dispatch import receiver

from django.forms.models import model_to_dict


class JobView(viewsets.ModelViewSet):
    queryset = models.Job.objects.all()
    serializer_class = JobSerializers
    pagination_class = CPageNumberPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ("job_name",)

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            request.data["scrape"] = request.data["scrape"] if request.data.has_key('scrape') else "30s"
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            # 添加到consul中
            c.put_kv("%s/%s/%s" % (settings.CONSUL_JOB_DIR,
                                       request.data["job_name"],
                                   settings.CONSUL_IP + ":" + str(settings.CONSUL_PORT)),
                     request.data["scrape"])
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            # 先在consul中删除修改之前的
            c.delete_kv("%s/%s" % (settings.CONSUL_JOB_DIR, instance.job_name),recurse=True)
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            # 修改consul中的数据
            c.put_kv("%s/%s/%s" % (settings.CONSUL_JOB_DIR,
                                   request.data["job_name"],
                                   settings.CONSUL_IP + ":" + str(settings.CONSUL_PORT)),
                     request.data["scrape"])
            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            c.delete_kv("%s/%s" % (settings.CONSUL_JOB_DIR, instance.job_name), recurse=True)
            obj = models.Application.objects.filter(job_id=instance.id).all()
            for i in obj:
                c.delete_kv("%s/%s.yml" % (settings.CONSUL_PROMETHEUS_RULES_DIR,i.application_name),recurse=True)
            for i in instance.tags.all():
                c.service_unregister(i.address, i.port)
            self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route(methods=['get'], permission_classes=[], url_path='getall')
    def get_all(self, request, pk=None):
        obj = models.Job.objects.all()
        serialzer = JobSerializers(obj, many=True)
        return Response(serialzer.data)

class TargetView(viewsets.ModelViewSet):
    queryset = models.Target.objects.all()
    serializer_class = TargetSerializers
    pagination_class = CPageNumberPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ("target_name",)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            #现在consul中删除注册的服务
            c.service_unregister(request.data['address'],request.data['port'])
            # print "xxxx",request.data
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            c.service_unregister(instance.address,instance.port)
            t = models.Job.objects.filter(pk=request.data["tags"]).first()
            target_name = "{ipaddress}:{port}@{tag_name}".format(ipaddress=request.data["address"],
                                                                port=request.data["port"],
                                                                tag_name=t.job_name.encode("utf-8"))
            request.data["target_name"] = target_name
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            # 注册服务
            t = models.Job.objects.filter(pk=request.data["tags"]).first()
            c.service_register(request.data["target_name"].encode("utf-8"),
                               request.data["address"].encode("utf-8"),
                               request.data["port"],
                               t.job_name.encode("utf-8"))
            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
        return Response(serializer.data)
    #
    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            self.perform_destroy(instance)
            c.service_unregister(instance.address,instance.port)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route(methods=['get'], permission_classes=[], url_path='getall')
    def get_all(self, request, pk=None):
        obj = models.Job.objects.all()
        serialzer = JobSerializers(obj, many=True)
        return Response(serialzer.data)

class Application(viewsets.ModelViewSet):
    queryset = models.Application.objects.all()
    serializer_class = ApplicationSerializers
    pagination_class = CPageNumberPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ("application_name",)

    @list_route(methods=['get'], permission_classes=[], url_path='getall')
    def get_all(self, request, pk=None):
        obj = models.Application.objects.all()
        serialzer = ApplicationSerializers(obj, many=True)
        return Response(serialzer.data)

    def create(self, request, *args, **kwargs):
        if not request.data.has_key("job"):
            obj, create = models.Job.objects.get_or_create(scrape="30s",job_name="mixin")
            request.data["job"] = obj.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            # 针对rules consul管理


            # 针对alertmanager 管理
            a_obj = AlterToConsul(instance.rules_name,instance.group.title)
            a_obj.del_alert()

            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            # 针对rules consul管理
            application_name = models.Application.objects.filter(
                pk=request.data["application_info"]).first().application_name
            p_obj = PromToConsul(application_name, request.data["rules_name"])
            p_obj.add_rules(request.data)

            # 针对alertmanager 管理
            title_name = mm.Role.objects.filter(pk=request.data["group"]).first().title
            a_obj = AlterToConsul(request.data["rules_name"],title_name)
            a_obj.add_alert(request.data)

            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
        return Response(serializer.data)


    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            self.perform_destroy(instance)
            c.delete_kv("%s/%s.yml" % (settings.CONSUL_PROMETHEUS_RULES_DIR,instance.application_name),recurse=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class Rules(viewsets.ModelViewSet):
    queryset = models.Rules.objects.all()
    serializer_class = RuleSerializers
    pagination_class = CPageNumberPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ("rules_name",)

    @list_route(methods=['get'], permission_classes=[], url_path='getall')
    def get_all(self, request, pk=None):
        obj = models.Rules.objects.all()
        serialzer = RuleSerializers(obj, many=True)
        return Response(serialzer.data)

    @list_route(methods=['get'], permission_classes=[], url_path='get-choices-info')
    def get_choices_info(self, request, pk=None):
        dict1 = {}
        dict1['mysql_level_montior_choices'] = [x[0] for x in choices.mysql_level_montior_choices]

        dict1['monitor_mode_choices'] = [x for x in choices.monitor_mode_choices]
        dict1['reslove_choices'] = [x for x in choices.resolve_choices]
        return Response(dict1)

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            print "rrrrrrrrrrrr",request.data["monitor_mode"]
            request.data["monitor_mode"] = ",".join(request.data["monitor_mode"])
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            # 针对rules consul管理
            application_name = models.Application.objects.filter(pk=request.data["application_info"]).first().application_name
            p_obj = PromToConsul(application_name,request.data["rules_name"])
            p_obj.add_rules(request.data)

            # 针对alertmanager 管理
            title_name = mm.Role.objects.filter(pk=request.data["group"]).first().title
            a_obj = AlterToConsul(request.data["rules_name"],title_name)
            a_obj.add_alert(request.data)
            # c.put_kv("%s/%s" % (settings.CONSUL_ALERTMANAGER_DIR,title_name),request.data["monitor_mode"])
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            # request.data["monitor_mode"] = ",".join(request.data["monitor_mode"])
            request.data["monitor_mode"] = ",".join(request.data["monitor_mode"])
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            # 针对rules consul管理
            p_obj = PromToConsul(instance.application_info.application_name, instance.rules_name)
            p_obj.del_rules()

            # 针对alertmanager 管理
            a_obj = AlterToConsul(instance.rules_name,instance.group.title)
            a_obj.del_alert()

            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            # 针对rules consul管理
            application_name = models.Application.objects.filter(
                pk=request.data["application_info"]).first().application_name
            p_obj = PromToConsul(application_name, request.data["rules_name"])
            p_obj.add_rules(request.data)

            # 针对alertmanager 管理
            title_name = mm.Role.objects.filter(pk=request.data["group"]).first().title
            a_obj = AlterToConsul(request.data["rules_name"],title_name)
            a_obj.add_alert(request.data)

            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            # 针对rules consul管理
            p_obj = PromToConsul(instance.application_info.application_name, instance.rules_name)
            p_obj.del_rules()

            # 针对alertmanager管理
            a_obj = AlterToConsul(instance.rules_name,instance.group.title)
            a_obj.del_alert()

            self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


def Sms(request):
    data = json.loads(request.body)
    mode = request.GET.get("mode")
    group = request.GET.get("group")
    data = data["alerts"]
    p_obj = Police(group)
    p_obj.get_msg(data)
    for i in mode.split(","):
        print "jjjjjj",i
        if hasattr(p_obj,i):
            func = getattr(p_obj,i)
            func(data)

    return JsonResponse({"status":"ok"})

class ConsulServiceCheck(mixins.ListModelMixin,viewsets.GenericViewSet):
    serializer_class = TargetOnlineOfflineSerializers
    def get_queryset(self):
        list1 = c.service_check_serializers()
        return list1

class ServerCount(mixins.ListModelMixin,viewsets.GenericViewSet):
    serializer_class = ServerCountSerializers

    def get_queryset(self):
        dict1 = {}
        dict1["count"] = len(models.Job.objects.all())
        list1 = []
        list1.append(dict1)
        return list1

class TargetCount(mixins.ListModelMixin,viewsets.GenericViewSet):
    serializer_class = TargetCountSerializers

    def get_queryset(self):
        dict1 = {}
        dict1["count"] = len(models.Target.objects.all())
        list1 = []
        list1.append(dict1)
        return list1

class ApplicationCount(mixins.ListModelMixin,viewsets.GenericViewSet):
    serializer_class = ApplicationCountSerializers

    def get_queryset(self):
        dict1 = {}
        dict1["count"] = len(models.Application.objects.all())
        list1 = []
        list1.append(dict1)
        return list1

class RulesCount(mixins.ListModelMixin,viewsets.GenericViewSet):
    serializer_class = RulesCountSerializers

    def get_queryset(self):
        dict1 = {}
        dict1["count"] = len(models.Rules.objects.all())
        list1 = []
        list1.append(dict1)
        return list1

class GetServiceTree(APIView):
    def get(self, request, *args, **kwargs):
        result = BaseResponse()
        get_service_tree_list = get_tree()
        result.data = get_service_tree_list
        return JsonResponse(result.__dict__)

class Msg(viewsets.ModelViewSet):
    # queryset = models.MsgNotitfy.objects.all()
    serializer_class = MsgSerializers
    # pagination_class = CPageNumberPagination
    # filter_backends = (filters.SearchFilter,)
    # search_fields = ("rules_name",)

    def get_queryset(self):
        list1 = []
        q = models.MsgNotitfy.objects.all().order_by("-last_edit_timestamp")
        for i in q:
            dict1 = {}
            dict1["level"] = i.level
            dict1["rules"] = i.rules
            dict1["monitor_level_choices"] = i.monitor_level_choices
            dict1["level_choices"] = i.monitor_level_choices
            dict1["create_timestamp"] = i.create_timestamp
            dict1["last_edit_timestamp"] = i.last_edit_timestamp
            key_name = "error_" + str(i.rules.id)
            dict1["repeat_num"] = r.get_inc(key_name)
            dict1["rule_name"] = i.rules.rules_name
            dict1["expr"] = i.rules.expr
            dict1["msg"] = i.msg
            list1.append(dict1)
        return list1

class HisMsg(viewsets.ModelViewSet):
    # queryset = models.MsgNotitfy.objects.all()
    serializer_class = HisMsgSerializers
    # pagination_class = CPageNumberPagination
    # filter_backends = (filters.SearchFilter,)
    # search_fields = ("rules_name",)

    def get_queryset(self):
        list1 = []
        q = models.HisMsgNotitfy.objects.all().order_by("-last_edit_timestamp")
        for i in q:
            dict1 = {}
            dict1["level"] = i.level
            dict1["rules"] = i.rules
            dict1["monitor_level_choices"] = i.monitor_level_choices
            dict1["level_choices"] = i.monitor_level_choices
            dict1["create_timestamp"] = i.create_timestamp
            dict1["last_edit_timestamp"] = i.last_edit_timestamp
            dict1["rule_name"] = i.rules.rules_name
            dict1["expr"] = i.rules.expr
            key_name = str(i.rules.id) + "_" + str(i.id)
            dict1["repeat_num"] = i.repeat_num
            dict1["msg"] = i.msg
            list1.append(dict1)
        return list1


@receiver(post_save,sender=models.MsgNotitfy)
def msg_post_save(sender, **kwargs):
    # today_time = get_today_time_format()
    key_name = "error_" + str(kwargs["instance"].rules.id)
    r.r_inc(key_name)

@receiver(post_delete,sender=models.MsgNotitfy)
def msg_post_delet_save(sender, **kwargs):
    today_time = get_today_time_format()
    key_name = str(kwargs["instance"].rules.id) + "_" + str(kwargs["instance"].id)
    r.mv_inc(key_name)


class MysqlToConsulView(APIView):
    def post(self, request):
        """
        mysql同步到consul中
        :param request:
        :return:
        """
        mysql_to_consul_obj = MysqlToConsul()
        mysql_to_consul_obj.mysql_to_consul_create()
        result = BaseResponse()
        result.status = "ok"
        return Response(result.__dict__)

class Silence(viewsets.ModelViewSet):
    queryset = models.Silence.objects.all().order_by("-endsAt")
    serializer_class = SilenceSerializers
    pagination_class = CPageNumberPagination
    # filter_backends = (filters.SearchFilter,)
    # search_fields = ("rules_name",)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        silenceID = AlertmanagerSilence.add_slicence(data=request.data)
        request.data["silence_id"] = silenceID
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        request.data["silence_id"] = instance.silence_id
        silenceID = AlertmanagerSilence.add_slicence(data=request.data)
        AlertmanagerSilence.delete_slicence(slicence_id=instance.silence_id)
        request.data["silence_id"] = silenceID
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        AlertmanagerSilence.delete_slicence(slicence_id=instance.silence_id)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)






