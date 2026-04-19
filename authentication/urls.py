from django.urls import path

from .views import CustomTokenObtainPairView, CustomTokenRefreshView, RequestPasswordResetView, ResetPasswordView

urlpatterns = [
    path('token', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('password/request-reset', RequestPasswordResetView.as_view()),
    path('password/reset', ResetPasswordView.as_view()),
]