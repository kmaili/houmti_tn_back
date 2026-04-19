from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView
from django.views.generic import TemplateView

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('', TemplateView.as_view(template_name='scalar.html'), name='scalar'),
    path('admin/', admin.site.urls),

    path('api/<version>/auth/', include('authentication.urls')),
    path('api/<version>/users/', include('users.urls')),
    path('api/<version>/portfolio/', include('portfolio.urls')),
    path('api/<version>/services/', include('services.urls')),
    path('api/<version>/media/', include('media_visualisation.urls')),
    path('api/<version>/districts/', include('districts.urls')),
    path('api/<version>/interactions/', include('interactions.urls')),
]
