# -*- coding:utf-8 -*-
#Author:chao Yan

from rest_framework.pagination import PageNumberPagination


class CPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    page_query_param = "page"
    max_page_size = 1000