from django.urls import path
from media_visualisation.views import SecureMediaView

urlpatterns = [
    path('visualization', SecureMediaView.as_view(), name='media_visualization'),
]
