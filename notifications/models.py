from django.db import models
from django.conf import settings

class Notification(models.Model):
    CHANNEL_CHOICES = [("INAPP", "InApp"), ("EMAIL", "Email")]
    TYPE_CHOICES = [
        ("INVITATION", "Invitation"),
        ("REMINDER", "Reminder"),
        ("TASK_ASSIGNED", "Task Assigned"),
        ("TASK_DUE", "Task Due"),
        ("MINUTES_SUBMITTED", "Minutes Submitted"),
        ("MINUTES_APPROVED", "Minutes Approved"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notif_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default="INAPP")

    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    send_status = models.CharField(max_length=20, default="PENDING")  # PENDING/SENT/FAILED

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["notif_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user_id} - {self.notif_type}"


class ReminderLog(models.Model):
    REM_TYPE = [
        ("MEETING_24H", "Meeting 24h"),
        ("MEETING_1H", "Meeting 1h"),
        ("TASK_24H", "Task 24h"),
        ("TASK_OVERDUE", "Task overdue"),
    ]

    reminder_type = models.CharField(max_length=30, choices=REM_TYPE)
    content_type = models.CharField(max_length=30)  # "meeting" یا "task"
    object_id = models.PositiveIntegerField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("reminder_type", "content_type", "object_id")
        indexes = [
            models.Index(fields=["reminder_type", "content_type", "object_id"]),
            models.Index(fields=["sent_at"]),
        ]

    def __str__(self):
        return f"{self.reminder_type} {self.content_type}:{self.object_id}"
