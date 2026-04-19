from django.urls import path

from services.views import DomainView, ServiceView

urlpatterns = [
    path('', ServiceView.as_view(), name='service_view'),
    path('domains', DomainView.as_view(), name='domain_view'),
]
