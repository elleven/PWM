# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import unicode_literals
from django.http import JsonResponse
from rest_framework.views import APIView
from mgmt import models
from mgmt.utils.response_result import BaseResponse
from rest_framework import viewsets
from mgmt.utils import model_choices
from mgmt.app_serializers import *
from mgmt.utils.auth import Authtication
# from mgmt.app_serializers import BlogListImgSerializer
from django.db.models import Count
from permission_init import permission_init
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from django.contrib.auth import logout,login,authenticate
from rest_framework import exceptions
from mgmt.utils.c_pagination import CPageNumberPagination
from mgmt.utils.model_choices import choices
from rest_framework import status
# from rest_framework import authentication
import json
from django.db.models import Q
from rest_framework import serializers
from rest_framework import viewsets, mixins
import time
from django.conf import settings
from rest_framework import filters
from mgmt.utils.permission import get_user_menu
from django.db.models import Count, Avg, Min, Sum
# Create your views here.


from django.dispatch import receiver
from django.db.models.signals import post_save
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework import filters
# from django_filters import rest_framework
from mgmt.utils.model_choices import DataChoices
import datetime

def md5(user):
    import hashlib
    import time
    ctime = str(time.time())
    m = hashlib.md5(bytes(user))
    m.update(bytes(ctime))
    return m.hexdigest()

class GetToken(APIView):
    # authentication_classes = []
    def post(self,request,*args,**kwargs):
        #1. 去request中获取IP
        #2. 访问记录

        result = BaseResponse()
        # try:
        user = request._request.POST.get('username')
        pwd = request._request.POST.get('password')
        print user,pwd
        # user_obj = models.UserInfo.objects.filter(name=user).first()
        # print "aaaaaaaaaa",a.password,a.check_password('123')
        user_obj = authenticate(username=user,password=pwd)
        # print "uuuuuu",user_obj
        # print "uuuuuuu",user_obj.check_password(pwd),user_obj.password
        if not user_obj:
            result.code = 1002
            result.message = '用户名或密码错误'
        else:
            login(request, user_obj)
            menu_list = get_user_menu(user_obj)
            # 为登录用户创建token
            token = md5(user)
            # 存在就更新 不存在就创建
            models.UserToken.objects.update_or_create(user=user_obj,defaults={'token':token})
            print "ssssss",token
            result.data = {"token":token,"menu_list":menu_list}
        # except Exception as e:
        #     result.code = 1003
        #     result.message = '服务器错误'
        return JsonResponse(result.__dict__)

class FirstLogin(APIView):
    import json
    def get(self,request):
        result = BaseResponse()

        user_obj = models.UserInfo.objects.all()
        result.code = 1001
        # 用户第一次登陆
        if len(user_obj) == 0:
            role_objs = permission_init()
            result.data = role_objs
            print "rrrrrrrrrr",result.data
            result.status = 1
        else:
            result.status = 2
        return JsonResponse(result.__dict__)

class UserView(viewsets.ModelViewSet):
    queryset = models.UserInfo.objects.all()
    serializer_class = UserSerializer
    pagination_class = CPageNumberPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name", "email")


    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        request.data.pop('password')
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @list_route(methods=['get'], url_path="get-my-info")
    def get_my_info(self, request, pk=None):
        # print "ppppp",request.user
        username = request._request.GET.get("username")
        try:
            serializer = self.get_serializer(request.user)
        except:
            obj = models.UserInfo.objects.filter(email=username).first()
            serializer = self.get_serializer(obj)
        try:
            return Response(serializer.data)
        except:
            return Response({})

    @list_route(methods=['post','put'], permission_classes=[], url_path='update-password')
    def update_password(self, request, pk=None):
        instance = request.user
        new_password = request.data.get("password")
        if not new_password:
            raise exceptions.ParseError("新密码不能为空")
        instance.set_password(new_password)
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @list_route(methods=['get'], permission_classes=[], url_path='getall')
    def get_all(self, request, pk=None):
        obj = models.UserInfo.objects.all()
        serialzer = UserSerializer(obj, many=True)
        return Response(serialzer.data)

class RoleViews(viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    queryset = models.Role.objects.all()
    pagination_class = CPageNumberPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)

    @list_route(methods=['get'], permission_classes=[], url_path='getall')
    def get_roles_info(self, request, pk=None):
        obj = models.Role.objects.all()
        serialzer = RoleSerializer(obj, many=True)
        print "sssssssss", serialzer.data
        return Response(serialzer.data)

class PermissionViews(viewsets.ModelViewSet):
    serializer_class = PermissionSerializer
    queryset = models.Permission.objects.all()
    pagination_class = CPageNumberPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)

    @list_route(methods=['get'], permission_classes=[], url_path='getall')
    def get_roles_info(self, request, pk=None):
        obj = models.Permission.objects.all()
        serialzer = PermissionSerializer(obj, many=True)
        return Response(serialzer.data)

class MenuViews(viewsets.ModelViewSet):
    serializer_class = MenuSerializer
    queryset = models.Menu.objects.all()
    pagination_class = CPageNumberPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)

    @list_route(methods=['get'], permission_classes=[], url_path='getall')
    def get_roles_info(self, request, pk=None):
        obj = models.Menu.objects.all()
        serialzer = MenuSerializer(obj, many=True)
        return Response(serialzer.data)
