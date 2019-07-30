# -*- coding:utf-8 -*-
#Author:chao Yan

from rest_framework.routers import SimpleRouter
from django.conf.urls import url
from monitor import views

router = SimpleRouter(trailing_slash=False)
router.register("job_manager", views.JobView, base_name='job_manager')
router.register("target_manager", views.TargetView, base_name='target_manager')
router.register("application_manager", views.Application, base_name='application_manager')
router.register("rules_manager", views.Rules, base_name='rules_manager')
router.register("consul_service_check", views.ConsulServiceCheck, base_name='consul_service_check')
router.register("server_total", views.ServerCount, base_name='server_total')
router.register("target_total", views.TargetCount, base_name='target_total')
router.register("application_total", views.ApplicationCount, base_name='application_total')
router.register("rules_total", views.RulesCount, base_name='rules_total')
router.register("monitor_msg", views.Msg, base_name='msg')
router.register("his_monitor_msg", views.HisMsg, base_name='his_msg')
router.register("slience", views.Silence, base_name='slience')
urlpatterns = [
    url(r'^sms$',views.Sms),
    url(r'^get_server_tree$',views.GetServiceTree.as_view()),
    url(r'^mysql_push_consul',views.MysqlToConsulView.as_view()),
]

urlpatterns += router.urls