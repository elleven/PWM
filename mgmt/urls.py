from rest_framework.routers import SimpleRouter
from django.conf.urls import url
from mgmt import views

router = SimpleRouter(trailing_slash=False)
router.register("user", views.UserView)
router.register("roles", views.RoleViews)
router.register("permission", views.PermissionViews)
router.register("menu", views.MenuViews)
# router.register("application_manager", views.ApplicationManager,base_name='applimanager')
# router.register("upload_file", views.BlogImgViewSet,base_name='uploadfile')
# router.register("resource_disk", views.ResourceDisk,base_name='resourcedisk')

urlpatterns = [
    url(r'^token/$',views.GetToken.as_view()),
    url(r'^first_login/$',views.FirstLogin.as_view()),
    # url(r'^data_import$',views.data_import),
]
urlpatterns += router.urls
