from rest_framework.pagination import PageNumberPagination

class UserNotificationPagination(PageNumberPagination):
    page_size = 10              # default items per page
    page_size_query_param = 'page_size'  # allow client to set page size
    max_page_size = 50 