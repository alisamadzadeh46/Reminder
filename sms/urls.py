from django.urls import path
from . import views

urlpatterns = [
    path("", views.sms_outbox, name="sms-outbox"),
    path("send/", views.sms_send, name="sms-send"),
    path("<int:pk>/", views.sms_detail, name="sms-detail"),
]