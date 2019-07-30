# -*- coding:utf-8 -*-
#Author:chao Yan

def get_user_menu(user_obj):
    roles_obj = user_obj.roles.filter(permissions__id__isnull=False).values('permissions__id',
                                                                            'permissions__alias',
                                                                            'permissions__name',
                                                                            'permissions__state',
                                                                            'permissions__icon',
                                                                            'permissions__menu_id',
                                                                            'permissions__pid_id',
                                                                            'permissions__pid__alias',
                                                                            'permissions__pid__name',
                                                                            'permissions__pid__state',
                                                                            'permissions__menu__alias',
                                                                            'permissions__menu__icon',
                                                                            'permissions__menu__state',
                                                                            )
    # print "rrrrrrrr",roles_obj
    menu_list = []
    menu_index = []

    for i in roles_obj:
        # print i["permissions__menu_id"]
        #判断菜单id是否再列表中，如果在获取索引值
        if i["permissions__menu_id"] in menu_index:
            index = menu_index.index(i["permissions__menu_id"])
            dict2 = {}
            dict2["entity"] = {}
            dict2["entity"]["id"] = i["permissions__id"]
            dict2["entity"]["icon"] = i["permissions__icon"]
            dict2["entity"]["alias"] = i["permissions__alias"]
            dict2["entity"]["state"] = i["permissions__state"]
            dict2["entity"]["name"] = i["permissions__name"]
            dict2["entity"]["sort"] = 0
            # dict2["entity"]["parentMenuId"] = i["permissions__menu_id"]
            dict2["entity"]["createUserId"] = 1
            dict2["entity"]["discription"] = i["permissions__alias"]
            # dict2["childs"] = "null"
            menu_list[index]["childs"].append(dict2)
        else:
            menu_index.append(i["permissions__menu_id"])
            dict1 = {}
            dict2 = {}
            dict1["entity"] = {}
            dict1["entity"]["id"] = i["permissions__menu_id"]
            dict1["entity"]["icon"] = i["permissions__menu__icon"]
            dict1["entity"]["alias"] = i["permissions__menu__alias"]
            dict1["entity"]["name"] = i["permissions__menu__alias"]
            dict1["entity"]["sort"] = 0
            dict1["entity"]["state"] = i["permissions__menu__state"]
            dict1["entity"]["createUserId"] = 1
            # dict1["entity"]["parentMenuId"] = 0
            dict1["entity"]["discription"] = i["permissions__menu__alias"]
            dict1["childs"] = []
            dict2["entity"] = {}
            dict2["entity"]["id"] = i["permissions__id"]
            dict2["entity"]["icon"] = i["permissions__icon"]
            dict2["entity"]["alias"] = i["permissions__alias"]
            dict2["entity"]["state"] = i["permissions__state"]
            dict2["entity"]["name"] = i["permissions__name"]
            dict2["entity"]["sort"] = 0
            dict2["entity"]["discription"] = i["permissions__alias"]
            # dict2["entity"]["parentMenuId"] = i["permissions__menu_id"]
            dict2["entity"]["createUserId"] = 1
            # dict2["childs"] = "null"
            dict1["childs"].append(dict2)
            menu_list.append(dict1)
    # print menu_list
    return menu_list


