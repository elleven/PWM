# -*- coding:utf-8 -*-
#Author:chao Yan

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PWM.settings")
import django

django.setup()

from mgmt.models import Menu, Permission, Role, UserInfo


def permission_init():
    print("==================================here")
    try:
        menu_list = [

            Menu(id=1, alias='系统管理', icon='glyphicon glyphicon-dashboard'),
            Menu(id=2, alias='监控', icon='glyphicon glyphicon-dashboard'),
        ]

        Menu.objects.bulk_create(menu_list)

        permission_list = [
            Permission(id=1, alias='用户管理', name='user-manager', icon='', menu_id=1),
            Permission(id=2, alias='用户组管理', name='user-group-manager', icon='', menu_id=1),
            Permission(id=3, alias='权限管理', name='permission-manager', icon='', menu_id=1),
            Permission(id=4, alias='菜单管理', name='menu-manager', icon='', menu_id=1),
            Permission(id=5, alias='监控首页', name='monitor-dashboard', icon='', menu_id=2),
            Permission(id=6, alias='Job管理', name='job-manager', icon='', menu_id=2),
            Permission(id=7, alias='监控数据源管理', name='target-manager', icon='', menu_id=2),
            Permission(id=8, alias='应用集管理', name='application-manager', icon='', menu_id=2),
            Permission(id=9, alias='规则管理', name='rule-manager', icon='', menu_id=2),
            Permission(id=10, alias='报警静默管理', name='monitor-silence', icon='', menu_id=2),

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
