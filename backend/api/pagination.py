from rest_framework.pagination import PageNumberPagination
from django.conf import settings


class RecipePagination(PageNumberPagination):
    page_size = settings.PAGE_SIZE
    page_size_query_param = "limit"
