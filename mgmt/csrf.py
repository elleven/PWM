# -*- coding:utf-8 -*-
#Author:chao Yan

class DisableCSRF(object):
    def process_request(self, request):
        print "===="
        setattr(request, '_dont_enforce_csrf_checks', True)