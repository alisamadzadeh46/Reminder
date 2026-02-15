from django.urls import path
from . import views

urlpatterns = [
    path("", views.sms_outbox, name="sms-outbox"),
    path("send/", views.sms_send, name="sms-send"),
    path("<int:pk>/", views.sms_detail, name="sms-detail"),
    path("delivery-report/", views.delivery_report, name="sms-delivery-report"),

    path("dashboard/", views.user_dashboard, name="user_dashboard"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),

]
