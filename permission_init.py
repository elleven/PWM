# -*- coding:utf-8 -*-
#Author:chao Yan

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PWM.settings")
import django

django.setup()

from mgmt.models import Menu, Permission, Role, UserInfo


def permission_init():
    # print("==================================here")
    try:
        menu_list = [

            Menu(id=1, alias='首页', icon='glyphicon glyphicon-dashboard'),
        ]

        Menu.objects.bulk_create(menu_list)

        permission_list = [
            Permission(id=1, alias='首页', name='/dashboard/', icon='glyphicon glyphicon-dashboard', menu_id=1),

        ]

        Permission.objects.bulk_create(permission_list)

        obj = Role.objects.create(id=1, title='超级管理员')
        obj.permissions.add(*range(1, len(permission_list) + 1))

        # user_obj = UserInfo.objects.filter(is_admin=True).first()
        # user_obj.roles.add(1)
    except:
        pass

    role_objs = Role.objects.all()
    from django.core import serializers
    data = serializers.serialize("json", role_objs)
    # list1 = [ x.id for x in role_objs ]
    return data

if __name__ == "__main__":
    permission_init()
