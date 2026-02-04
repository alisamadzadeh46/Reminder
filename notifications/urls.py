# notifications/urls.py
from django.urls import path
from .views import my_notifications, mark_notification_read

urlpatterns = [
    path("my/", my_notifications, name="my-notifications"),
    path("<int:pk>/read/", mark_notification_read, name="notification-read"),
]
