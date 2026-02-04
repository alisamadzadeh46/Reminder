from django.urls import path
from .views import *

urlpatterns = [
    path("my/", MyMeetingsListView.as_view(), name="my-meetings"),
    path("create/", MeetingCreateView.as_view(), name="meeting-create"),
    path("<int:pk>/", MeetingDetailView.as_view(), name="meeting-detail"),
    path("<int:pk>/rsvp/", meeting_rsvp, name="meeting-rsvp"),
    path("<int:meeting_id>/invitees/add/", add_invitee, name="meeting-add-invitee"),
]
