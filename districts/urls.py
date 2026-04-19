from django.urls import path
from .views import DisctrictView, UserDistrictView

urlpatterns = [
    path('', DisctrictView.as_view(), name='districts'),
    path('from-location', UserDistrictView.as_view(), name='districts_from_location'),
]
