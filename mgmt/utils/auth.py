# -*- coding:utf-8 -*-
#Author:chao Yan

from django.shortcuts import render,HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from mgmt import models
from rest_framework.authentication import BaseAuthentication


class Authtication(object):
    """
    认证
    """
    #名字必须要authenticate
    def authenticate(self,request):
        token = request._request.GET.get('token')
        print "=============",token
        token_obj = models.UserToken.objects.filter(token=token).first()
        from rest_framework import exceptions
        if not token_obj:
            """
            认证失败
            """
            raise exceptions.AuthenticationFailed('用户认证失败')
        #在restframework 内部会将这两个字段赋值给request，以供后续操作使用
        return (token_obj.user,token_obj)

    def authenticate_header(self, request):
        """
        必须有 否则报错
        :param request:
        :return:
        """
        pass