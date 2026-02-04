# notifications/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Notification

@login_required
def my_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "notifications/my_notifications.html", {
        "notifications": notifications
    })

@login_required
def mark_notification_read(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.is_read = True
    n.save(update_fields=["is_read"])
    return redirect("my-notifications")
