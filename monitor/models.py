# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
# from django.contrib.postgres.fields import JSONField


import sys
reload(sys)
sys.setdefaultencoding('utf8')

from mgmt.utils.model_choices import choices


class Job(models.Model):
    """
    Job的配置
    """
    job_name = models.CharField(max_length=32,unique=True)
    scrape = models.CharField(max_length=32,null=True,blank=True,verbose_name='采集间隔')

class Target(models.Model):
    """
    监控数据源
    """
    target_name = models.CharField(max_length=128,null=True)
    address = models.CharField(max_length=64)
    port = models.IntegerField()
    tags = models.ForeignKey(to='Job', related_name='tags',verbose_name='所属的Job', null=True, blank=True, help_text="此项是prometheus配置job中要匹配的target，"
                                                                                               "也就是哪类target属于那个job")
    status = models.CharField(choices=choices.status_choices,null=True,verbose_name='是否可用',max_length=32)
    # check_url = models.CharField(max_length=128,verbose_name="服务注册时，检测的url")
    # check_interval = models.CharField(max_length=64,verbose_name="检测的间隔")

class Application(models.Model):
    application_name = models.CharField(max_length=128)
    job = models.ForeignKey(to='Job',related_name='app',verbose_name='关联的数据源',null=True,blank=True)


    class Meta:
        verbose_name = '应用集管理'
        verbose_name_plural = verbose_name

class Rules(models.Model):
    rules_name = models.CharField(max_length=128)
    expr = models.CharField(max_length=256,verbose_name="报警规则")
    long_time = models.CharField(max_length=64,verbose_name="持续多久报警")
    mysql_file_montior_info = models.CharField(choices=choices.mysql_level_montior_choices, null=True, verbose_name='报警级别',max_length=32)
    application_info = models.ForeignKey(to="Application",verbose_name="关联的应用集",null=True,blank=True,related_name="app_info")
    group = models.ForeignKey(to="mgmt.Role",related_name="rules_group",null=True,blank=True,verbose_name="所属于的报警组")
    summary = models.CharField(max_length=512,verbose_name="报警总结")
    desc = models.CharField(max_length=512,verbose_name="报警描述")
    monitor_mode = models.CharField(null=True, verbose_name='报警方式',max_length=32)
    repeat_time = models.CharField(max_length=32,null=True,blank=True,verbose_name="报警间隔")
    resolve = models.CharField(choices=choices.resolve_choices,null=True,verbose_name='是否通知',max_length=32)

    class Meta:
        verbose_name = '报警规则'
        verbose_name_plural = verbose_name

class MsgNotitfy(models.Model):
    level = models.CharField(max_length=32)
    rules = models.ForeignKey(to="Rules",related_name="msg",verbose_name="所属的规则",null=True,blank=True,on_delete=models.CASCADE)
    monitor_level_choices = models.CharField(choices=choices.montior_status_choices,null=True,verbose_name="报警状态",max_length=32)
    create_timestamp = models.DateTimeField(auto_now_add=True)
    last_edit_timestamp = models.DateTimeField(auto_now=True)
    msg = models.TextField(null=True,blank=True,verbose_name="报警内容")

    class Meta:
        verbose_name = '报警记录'
        verbose_name_plural = verbose_name

class HisMsgNotitfy(models.Model):
    repeat_num = models.IntegerField(null=True,blank=True)
    level = models.CharField(max_length=32)
    rules = models.ForeignKey(to="Rules",related_name="hismsg",verbose_name="所属的规则",null=True,blank=True,on_delete=models.CASCADE)
    monitor_level_choices = models.CharField(choices=choices.montior_status_choices,null=True,verbose_name="报警状态",max_length=32)
    create_timestamp = models.DateTimeField()
    last_edit_timestamp = models.DateTimeField()
    msg = models.TextField(null=True,blank=True,verbose_name="报警内容")

    class Meta:
        verbose_name = '历史报警记录'
        verbose_name_plural = verbose_name

class Silence(models.Model):
    silence_id = models.CharField(max_length=128, null=True, default="null")
    startsAt = models.DateTimeField()
    endsAt = models.DateTimeField()
    createdBy = models.CharField(max_length=32)
    comment = models.CharField(max_length=128)
    matchers = models.CharField(max_length=512)

    class Meta:
        verbose_name = '配置报警静默表'
        verbose_name_plural = verbose_name
