# -*- coding:utf-8 -*-
#Author:chao Yan

from mgmt import models

class DataChoices(object):
    device_type = [
                '物理服务器',
                '公有云服务器',
                '私有云服务器',
                '虚拟机',
                '交换机',
                '防火墙',
                '数据库',
                '安全专用机',
                '决策系统专用机',
                '云专用机',
                'AI专用机',
                'ERP专用机',
                '客服专用机',
                '大数据专用机',
                '宿主机',
                '无',
                'ERP数据库'
                '应用',
                '其他'
            ]
    device_status = [
        '上架',
        '运行中',
        '离线',
        '下架',
        '优化关机',
        '已关机',
        '待关机'
    ]
    env_type = [
        '准生产环境',
        '开发测试环境',
        '生产环境',
        '办公环境',
        '管理环境',
        '无'
    ]
    select_dict = {
        "manager":"技术负责人",
        "sys_name":"操作系统",
        "device_env_type_name":"所属环境",
        "bussiness_name":"业务条线",
        "idc_name":"IDC机房",
        "device_status_name":"设备运行状态",
        "device_type_name":"机器类型",
        "ipaddress":"IPADDRESS",
        "second_name":"二级产品线",
        "purpose":"用途",
        "sn":"SN号",
        "first_name":"一级产品线",
        "业务系统":"业务系统"
    }

    replace_dict = {
        "sys_name": "操作系统",
        "device_env_type_id": "所属环境",
        "idc": "IDC机房",
        "device_status_id": "设备运行状态",
        "second_business": "二级产品线",
        "purpose": "用途",
    }

    mysql_file_montior = (
        (0, "异常"),
        (1, "未开始"),
        (2, "完成")
    )

    mysql_level_montior_choices = (
        ("warning", "warning"),
        ("error", "error"),
        ("critical", "critical"),
    )

    monitor_mode_choices = (
        ("sms", "短信"),
        ("sendmail", "邮件"),
        ("wx", "企业微信"),
    )

    resolve_choices = (
        ("true","true"),
        ("false","false"),
    )

    status_choices = (
        ("true", "true"),
        ("false", "false"),
    )

    montior_status_choices = (
        ("firing", "未解决"),
        ("resolved", "已解决"),
    )

choices = DataChoices()
