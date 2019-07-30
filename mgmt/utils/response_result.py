# -*- coding:utf-8 -*-
#Author:chao Yan

class BaseResponse(object):
    def __init__(self):
        self.code = 200
        self.message = None
        self.data = None
        self.status = None
        self.error = None