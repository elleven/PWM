#coding:utf-8
#Author:chao Yan


import re
import logging
import datetime

from rest_framework import serializers
from rest_framework import exceptions
from mgmt.models import UserInfo
from mgmt.models import Menu
from mgmt.models import Permission
from mgmt.models import Role
from mgmt.utils.model_choices import DataChoices


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(label="邮箱")
    password = serializers.CharField(required=False, min_length=6, max_length=20, label="密码")

    def create(self, validated_data):
        user = UserInfo.objects.create_user(name=validated_data["name"],email=validated_data["email"],password=validated_data["password"])
        user.roles.add(*validated_data["roles"])
       

        try:
            pass
        except Exception as exc:
            pass
        return user

    class Meta:
        model = UserInfo
        exclude = ("is_staff","is_active","is_admin","is_superuser")

class UserListField(serializers.RelatedField):
    def to_representation(self, value):
        name = value.name
        return name

    def to_internal_value(self, data):
        if isinstance(data,int):
            return self.get_queryset().get(pk=data)
        else:
            return self.get_queryset().get(name=data)

from rest_framework import serializers


class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = '__all__'

class PermissionSerializer(serializers.ModelSerializer):

    menu_info = serializers.CharField(source="menu.alias", read_only=True)
    pid_info = serializers.CharField(source="pid.alias", read_only=True)

    class Meta:
        model = Permission
        fields = '__all__'

class UserInfoSerializer(serializers.ModelSerializer):
    roles_info = serializers.CharField(source="roles.title", read_only=True)

    class Meta:
        model = UserInfo
        fields = ("email","name","roles")


class RoleSerializer(serializers.ModelSerializer):
    permission_info = serializers.CharField(source="permissions.alias", read_only=True)

    class Meta:
        model = Role
        fields = '__all__'
