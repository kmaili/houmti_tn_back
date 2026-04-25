from django.urls import path
from interactions.views import ArtisanReviewListView
from .views import ArtisanSearch, ClientRegisterView, ArtistRegisterView, Favorites, UserDetailView, UserNotificationView, VerifyOTPView

urlpatterns = [
    path('register/client', ClientRegisterView.as_view(), name='register_client'),
    path('register/artisan', ArtistRegisterView.as_view(), name='register_artist'),
    path('register/verify', VerifyOTPView.as_view(), name='verify_otp'),
    path('me', UserDetailView.as_view(), name='user_detail'),
    path('me/notifications', UserNotificationView.as_view(), name='user_notifications'),
    path('me/notifications/all/read', UserNotificationView.as_view(), name='mark_all_notifications_read'),
    path('me/notifications/<int:pk>/read', UserNotificationView.as_view(), name='mark_notification_read'),
    path('artisans/<int:pk>', UserDetailView.as_view(), name='artisan_details'),
    path('artisans/search', ArtisanSearch.as_view(), name='search_artisans'),
    path('artisans/favorites', Favorites.as_view(), name='favorites_artisans'),
    path('artisans/<int:artist_id>/reviews', ArtisanReviewListView.as_view(), name='artisan_reviews'),
]