from interactions.views import BookingView, CreateMessageView, DiscussionMessagesView, JobView, MyDiscussionsView
from django.urls import path

urlpatterns = [
    path('bookings', BookingView.as_view(), name='manage_bookings'),
    path('jobs', JobView.as_view(), name='manage_jobs'),
    path('jobs/<int:pk>', JobView.as_view(), name='job_details'),
    path("discussions", MyDiscussionsView.as_view()),
    path("discussions/<int:discussion_id>/messages", DiscussionMessagesView.as_view()),
    path("messages", CreateMessageView.as_view()),
]
