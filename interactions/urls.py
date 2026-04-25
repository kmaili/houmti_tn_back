from interactions.views import BookingView, CreateMessageView, DiscussionMessagesView, DiscussionReadAllMessages, JobView, MyDiscussionsView, ReviewDetailView, ReviewView
from django.urls import path

urlpatterns = [
    path('bookings', BookingView.as_view(), name='manage_bookings'),
    path('jobs', JobView.as_view(), name='manage_jobs'),
    path('jobs/<int:pk>', JobView.as_view(), name='job_details'),
    path("discussions", MyDiscussionsView.as_view()),
    path("discussions/<int:discussion_id>/messages", DiscussionMessagesView.as_view()),
    path("discussions/<int:discussion_id>/read", DiscussionReadAllMessages.as_view()),
    path("messages", CreateMessageView.as_view()),
    path('reviews', ReviewView.as_view(), name='reviews'),
    path('reviews/<int:pk>', ReviewDetailView.as_view(), name='review_detail'),
]
