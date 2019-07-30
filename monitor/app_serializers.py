# -*- coding:utf-8 -*-
#Author:chao Yan

from rest_framework import serializers
from monitor import models
from mgmt import models as mm
from monitor.utils.consulapi import c
from mgmt.utils.model_choices import choices
import json

class JobSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.Job
        fields = '__all__'

class TargetSerializers(serializers.ModelSerializer):
    job_name = serializers.CharField(source="tags.job_name", read_only=True)
    target_name = serializers.CharField(read_only=True)

    def create(self, validated_data):
        target_name = "{ip}:{port}@{job_name}".format(ip=validated_data["address"],
                                                      port=validated_data["port"],
                                                      job_name=validated_data["tags"].job_name)
        validated_data["target_name"] = target_name
        table = models.Target.objects.create(**validated_data)
        c.service_register(target_name,validated_data["address"],validated_data["port"],validated_data["tags"].job_name)
        return table

    class Meta:
        model = models.Target
        fields = '__all__'

class ApplicationSerializers(serializers.ModelSerializer):
    # job = JobListField(many=True,queryset=models.Job.objects.all())

    job_name_info = serializers.CharField(source="job.job_name", read_only=True)

    class Meta:
        model = models.Application
        fields = '__all__'


class GroupListField(serializers.RelatedField):
    def to_representation(self, value):
        name = value.title
        return name

    def to_internal_value(self, data):
        if isinstance(data,int):
            return self.get_queryset().get(pk=data)
        else:
            return self.get_queryset().get(title=data)

class DisplayChoices(serializers.RelatedField):
    """
    自定义字段
    """
    def to_representation(self, value):
        return value

class RuleSerializers(serializers.ModelSerializer):
    # job = JobListField(many=True,queryset=models.Job.objects.all())

    application_infos = serializers.CharField(source="application_info.application_name", read_only=True)
    group_info = serializers.CharField(source="group.title", read_only=True)
    # device_type = serializers.CharField(source='monitor_mode_choices', read_only=True)
    # monitor_mode_choices = DisplayChoices(read_only=True)

    class Meta:
        model = models.Rules
        fields = '__all__'

class TargetOnlineOfflineSerializers(serializers.Serializer):
    name = serializers.CharField()
    value = serializers.IntegerField()

class ServerCountSerializers(serializers.Serializer):
    count = serializers.IntegerField()

class TargetCountSerializers(serializers.Serializer):
    count = serializers.IntegerField()

class ApplicationCountSerializers(serializers.Serializer):
    count = serializers.IntegerField()

class RulesCountSerializers(serializers.Serializer):
    count = serializers.IntegerField()

class MsgSerializers(serializers.ModelSerializer):
    level_choices = serializers.CharField(source='monitor_level_choices', read_only=True)
    monitor_level_choices = DisplayChoices(read_only=True)
    rule_name = serializers.CharField(source="rules.rules_name", read_only=True)
    expr = serializers.CharField(source="rules.expr", read_only=True)
    create_timestamp = serializers.DateTimeField(format="%H:%M:%S", required=False, read_only=True)
    last_edit_timestamp = serializers.DateTimeField(format="%H:%M:%S", required=False, read_only=True)
    repeat_num = serializers.IntegerField(read_only=True)
    # create_timestamp = serializers.TimeField(format="%H:%M:%S", input_formats=None)
    # last_edit_timestamp = serializers.TimeField(format="%H:%M:%S", input_formats=None)


    class Meta:
        model = models.MsgNotitfy
        fields = '__all__'

class HisMsgSerializers(serializers.ModelSerializer):
    level_choices = serializers.CharField(source='monitor_level_choices', read_only=True)
    monitor_level_choices = DisplayChoices(read_only=True)
    rule_name = serializers.CharField(source="rules.rules_name", read_only=True)
    expr = serializers.CharField(source="rules.expr", read_only=True)
    create_timestamp = serializers.DateTimeField(format="%H:%M:%S", required=False, read_only=True)
    last_edit_timestamp = serializers.DateTimeField(format="%H:%M:%S", required=False, read_only=True)
    repeat_num = serializers.IntegerField(read_only=True)
    # create_timestamp = serializers.TimeField(format="%H:%M:%S", input_formats=None)
    # last_edit_timestamp = serializers.TimeField(format="%H:%M:%S", input_formats=None)


    class Meta:
        model = models.HisMsgNotitfy
        fields = '__all__'


class JSONSerializerField(serializers.Field):
    """Serializer for JSONField -- required to make field writable"""

    def to_representation(self, value):
        json_data = {}
        try:
            json_data = json.loads(value)
        except ValueError as e:
            raise e
        finally:
            return json_data

    def to_internal_value(self, data):
        return json.dumps(data)


class SilenceSerializers(serializers.ModelSerializer):
    matchers = JSONSerializerField()
    startsAt = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", input_formats=None)
    endsAt = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", input_formats=None)

    class Meta:
        model = models.Silence
        fields = '__all__'
