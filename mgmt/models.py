# -*- coding:utf-8 -*-
# Author:chao Yan
from django.db import models
# from mgmt.utils.model_choices import choices
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)

import sys

reload(sys)

sys.setdefaultencoding('utf8')


class Menu(models.Model):
    """
    一级菜单
    """

    alias = models.CharField(verbose_name="一级菜单名称", max_length=32)
    state = models.CharField(verbose_name="是否启用", max_length=32, default="ENABLE")
    icon = models.CharField(verbose_name='图标', max_length=32, null=True, blank=True, help_text='菜单才设置图标')

    def __str__(self):
        return self.title


class Permission(models.Model):
    """ 
    权限表    
    """
    # 二级菜单的名字
    alias = models.CharField(verbose_name='标题', max_length=32)
    # 二级菜单的url 
    name = models.CharField(verbose_name='url所对应的前端路由名称', max_length=128)
    # 是否可以做菜单 
    icon = models.CharField(verbose_name='图标', max_length=32, null=True, blank=True, help_text='菜单才设置图标')
    state = models.CharField(verbose_name="是否启用", max_length=32, default="ENABLE")
    # web_component = models.CharField(verbose_name="前端对应挂载目录",max_length=64,null=True,blank=True)
    # is_menu = models.BooleanField(verbose_name='是否是菜单', default=False)

    menu = models.ForeignKey(to='Menu', verbose_name='所属菜单', null=True, blank=True, help_text='null表示不是菜单;非null表示2级菜单')

    pid = models.ForeignKey(to='self', related_name='parent', null=True, blank=True, verbose_name='关联权限',
                            help_text='对于非菜单权限，需要选择一个可以成为菜单的权限，用户做默认展开和选中菜单')

    class Meta:
        verbose_name_plural = '权限表'

    def __str__(self):
        return self.title


class Role(models.Model):
    """
    角色
    """
    title = models.CharField(verbose_name='角色名称', max_length=32)
    permissions = models.ManyToManyField(verbose_name='拥有的所有权限', to='Permission', blank=True)

    class Meta:
        verbose_name_plural = '角色表'

    def __str__(self):
        return self.title


class UserProfileManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        """
        创建普通用户
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            # 验证邮件地址是否合法
            email=self.normalize_email(email),
            name=name,
        )

        # 把密码加密
        user.set_password(password)
        # 保存普通用户
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password):
        """
        创建超级用户
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
            name=name,
        )
        user.is_admin = True
        # 如果不配置is_staff 用户登录django admin不了
        user.is_staff = True
        user.save(using=self._db)
        return user


class UserInfo(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    wx_id = models.IntegerField(null=True,blank=True)
    # 自己添加的
    name = models.CharField(max_length=64)
    phone = models.CharField(max_length=64,null=True,blank=True)
    # password = models.CharField(_('password'), max_length=128)
    # password = models.CharField(verbose_name='密码', max_length=64)
    roles = models.ManyToManyField(verbose_name='拥有的所有角色', to='Role', related_name="group",blank=True)
    # 以下非自己添加，django用户认证必加的
    # date_of_birth = models.DateField()
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=True)
    is_staff = models.BooleanField(
        ("staff status"),
        default=True,
        help_text=("Designates whether the user can log into this admin site."),
    )
    # 创建用户的时候走这里必须这么写 python manage.py createsuperuser时
    objects = UserProfileManager()
    # 让email做用户名
    USERNAME_FIELD = 'email'
    # 必须要有什么字段,要求name必须填写
    REQUIRED_FIELDS = ["name"]
    ##get_full_name和get_short_name必须得有 django要求的
    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    def __unicode__(self):
        return '%s' % (self.name)
    
class UserToken(models.Model):
    token = models.CharField(max_length=64)
    user = models.OneToOneField(to='UserInfo')
