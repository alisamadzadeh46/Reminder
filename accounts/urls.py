from django.urls import path
from django.contrib.auth import views as auth_views

from .views import *

urlpatterns = [
    path("", dashboard, name="dashboard"),

    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),

    # خروج: اول صفحه تأیید (اختیاری)، بعد POST به logout
    path("logout/", logout_confirm_view, name="logout-confirm"),
    path("logout/do/", auth_views.LogoutView.as_view(), name="logout"),
]
