from django.contrib import admin
from .models import Notification, ReminderLog

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "notif_type", "channel", "is_read", "send_status", "created_at")
    list_filter = ("notif_type", "channel", "is_read", "send_status")
    search_fields = ("user__username", "title", "message")
    autocomplete_fields = ("user",)

@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    list_display = ("reminder_type", "content_type", "object_id", "sent_at")
    list_filter = ("reminder_type", "content_type", "sent_at")
    search_fields = ("object_id",)
